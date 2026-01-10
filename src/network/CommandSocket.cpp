#include "CommandSocket.hpp"

#include "Definitions.hpp"

#include <bits/types/struct_timeval.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include <algorithm>
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
    auto addr       = sockaddr_un{};
    addr.sun_family = AF_UNIX;
    copySocketPath(std::span{addr.sun_path}, socketPath_);

    [[maybe_unused]] const auto _ = connect(clientFd, reinterpret_cast<const sockaddr*>(&addr), sizeof(addr));
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
    std::cerr << "Błąd tworzenia socketu\n";
    return false;
  }

  auto addr       = sockaddr_un{};
  addr.sun_family = AF_UNIX;
  copySocketPath(std::span{addr.sun_path}, socketPath_);

  if (bind(serverFd_, reinterpret_cast<const sockaddr*>(&addr), sizeof(addr)) < 0)
  {
    std::cerr << "Błąd bind socketu\n";
    close(serverFd_);
    serverFd_ = -1;
    return false;
  }

  constexpr int32_t backlog = 5;
  if (listen(serverFd_, backlog) < 0)
  {
    std::cerr << "Błąd listen na sockecie\n";
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
        std::cerr << "Błąd select na sockecie\n";
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
        std::cerr << "Błąd accept połączenia\n";
      }
      continue;
    }

    if (shouldStop_.load(std::memory_order_acquire))
    {
      close(clientFd);
      break;
    }

    handleClient(clientFd);
    close(clientFd);
  }
}

void CommandSocket::handleClient(int32_t clientFd)
{
  uint8_t    cmdByte   = 0;
  const auto bytesRead = recv(clientFd, &cmdByte, sizeof(cmdByte), 0);

  if (bytesRead != static_cast<ssize_t>(sizeof(cmdByte)))
  {
    return;
  }

  if (cmdByte > static_cast<uint8_t>(IpcCommands::QUIT_GAME))
  {
    std::cerr << "Nieprawidłowa komenda: " << static_cast<int>(cmdByte) << '\n';
    return;
  }

  const auto command = static_cast<IpcCommands>(cmdByte);

  if (callback_)
  {
    callback_(command);
  }

  constexpr uint8_t ack = 1;
  send(clientFd, &ack, sizeof(ack), 0);
}

void CommandSocket::copySocketPath(const std::span<char> destinationBuffer, const std::string& source) noexcept
{
  const auto copySize = std::min(destinationBuffer.size() - 1, source.size());
  std::copy_n(source.data(), copySize, destinationBuffer.data());
  destinationBuffer[copySize] = '\0';
}

}  // namespace SnakeGame
