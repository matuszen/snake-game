#include "CommandSocket.hpp"

#include "Definitions.hpp"

#include <asm-generic/socket.h>
#include <bits/types/struct_timeval.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <span>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace SnakeGame
{

CommandSocket::CommandSocket(std::string socketPath)
  : shouldStop_(false), socketPath_(std::move(socketPath)), serverFd_(-1), initialized_(false)
{
}

CommandSocket::~CommandSocket()
{
  stop();
  cleanupSocket();
}

auto CommandSocket::start(CommandCallback callback) -> bool
{
  if (initialized_ or serverThread_ != nullptr)
  {
    return false;
  }

  callback_ = std::move(callback);

  if (not initializeSocket())
  {
    return false;
  }

  shouldStop_   = false;
  serverThread_ = std::make_unique<std::thread>(&CommandSocket::serverThreadFunction, this);
  initialized_  = true;

  return true;
}

void CommandSocket::stop()
{
  if (not initialized_ or serverThread_ == nullptr)
  {
    return;
  }

  shouldStop_ = true;

  const auto clientFd = socket(AF_UNIX, SOCK_STREAM, 0);
  if (clientFd >= 0)
  {
    constexpr uint32_t addrSize = sizeof(sockaddr_un);
    auto               addr     = sockaddr_un{};

    addr.sun_family = AF_UNIX;
    copySocketPath(std::span{addr.sun_path}, socketPath_);

    [[maybe_unused]] const auto _ = connect(clientFd, reinterpret_cast<const sockaddr*>(&addr), addrSize);
    close(clientFd);
  }

  if (serverThread_->joinable())
  {
    serverThread_->join();
  }

  serverThread_.reset();
  initialized_ = false;
}

auto CommandSocket::isRunning() const noexcept -> bool
{
  return initialized_ and not shouldStop_;
}

auto CommandSocket::initializeSocket() -> bool
{
  unlink(socketPath_.c_str());

  serverFd_ = socket(AF_UNIX, SOCK_STREAM, 0);
  if (serverFd_ < 0)
  {
    std::cerr << "Error creating socket\n";
    return false;
  }
  constexpr uint32_t addrSize = sizeof(sockaddr_un);
  auto               addr     = sockaddr_un{};
  addr.sun_family             = AF_UNIX;
  copySocketPath(std::span{addr.sun_path}, socketPath_);

  if (bind(serverFd_, reinterpret_cast<const sockaddr*>(&addr), addrSize) < 0)
  {
    std::cerr << "Error binding socket\n";
    close(serverFd_);
    serverFd_ = -1;
    return false;
  }

  constexpr int32_t backlog = 5;
  if (listen(serverFd_, backlog) < 0)
  {
    std::cerr << "Error listening on socket\n";
    close(serverFd_);
    serverFd_ = -1;
    return false;
  }

  return true;
}

void CommandSocket::cleanupSocket() noexcept
{
  if (serverFd_ >= 0)
  {
    close(serverFd_);
    serverFd_ = -1;
  }

  unlink(socketPath_.c_str());
}

void CommandSocket::serverThreadFunction()
{
  constexpr auto timeoutMs = std::chrono::milliseconds{100};

  while (not shouldStop_.load(std::memory_order_acquire))
  {
    fd_set readfds{};
    FD_ZERO(&readfds);
    FD_SET(serverFd_, &readfds);

    auto timeout = timeval{
      .tv_sec  = 0,
      .tv_usec = std::chrono::duration_cast<std::chrono::microseconds>(timeoutMs).count(),
    };

    const auto result = select(serverFd_ + 1, &readfds, nullptr, nullptr, &timeout);

    if (result < 0)
    {
      if (errno != EINTR)
      {
        std::cerr << "Error during select on socket\n";
      }
      continue;
    }

    if (result == 0)
    {
      continue;
    }

    const auto clientFd = accept(serverFd_, nullptr, nullptr);
    if (clientFd < 0)
    {
      if (errno != EINTR and errno != EAGAIN)
      {
        std::cerr << "Error accepting connection\n";
      }
      continue;
    }

    if (shouldStop_.load(std::memory_order_acquire))
    {
      close(clientFd);
      break;
    }

    constexpr uint32_t timevalSize = sizeof(timeval);
    constexpr auto     recvTimeout = timeval{
          .tv_sec  = 1,
          .tv_usec = 0,
    };

    if (setsockopt(clientFd, SOL_SOCKET, SO_RCVTIMEO, &recvTimeout, timevalSize) < 0)
    {
      std::cerr << "Error setting timeout on socket\n";
    }

    handleClient(clientFd);
    close(clientFd);
  }
}

void CommandSocket::handleClient(const int32_t clientFd)
{
  constexpr auto commandBufferSize = sizeof(uint8_t);
  uint8_t        commandByte       = 0;

  const auto bytesRead = recv(clientFd, &commandByte, commandBufferSize, 0);

  if (bytesRead < 0)
  {
    if (errno == EAGAIN or errno == EWOULDBLOCK)
    {
      return;
    }
    std::cerr << "Error during recv" << "\n";
    return;
  }

  if (bytesRead != static_cast<ssize_t>(commandBufferSize))
  {
    return;
  }

  if (commandByte > static_cast<uint8_t>(IpcCommands::CHANGE_BOARD_SIZE))
  {
    std::cerr << "Invalid command: " << static_cast<int32_t>(commandByte) << '\n';
    return;
  }

  const auto           command = static_cast<IpcCommands>(commandByte);
  std::vector<uint8_t> payload;

  if (command == IpcCommands::CHANGE_BOARD_SIZE)
  {
    std::array<uint8_t, 2> buf{};

    const size_t bytes = recv(clientFd, buf.data(), buf.size(), 0);
    if (bytes != buf.size())
    {
      std::cerr << "Error during reading CHANGE_BOARD_SIZE command\n";
      return;
    }
    payload.assign(std::begin(buf), std::end(buf));
  }

  if (callback_)
  {
    callback_(command, payload);
  }
  constexpr auto    ackSize = sizeof(uint8_t);
  constexpr uint8_t ack     = 1;
  send(clientFd, &ack, ackSize, 0);
}

void CommandSocket::copySocketPath(const std::span<char> destinationBuffer, const std::string& source) noexcept
{
  const auto copySize = std::min(destinationBuffer.size() - 1, source.size());
  std::copy_n(source.data(), copySize, destinationBuffer.data());
  destinationBuffer[copySize] = '\0';
}

}  // namespace SnakeGame
