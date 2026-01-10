#pragma once

#include "Definitions.hpp"

#include <atomic>
#include <cstdint>
#include <memory>
#include <span>
#include <string>
#include <thread>

namespace SnakeGame
{

class CommandSocket
{
public:
  explicit CommandSocket(std::string socketPath = std::string{DEFAULT_SOCKET_PATH});
  ~CommandSocket();

  CommandSocket(const CommandSocket& other)                   = delete;
  CommandSocket(CommandSocket&& other)                        = delete;
  auto operator=(const CommandSocket& other) -> CommandSocket = delete;
  auto operator=(CommandSocket&& other) -> CommandSocket      = delete;

  auto start(CommandCallback callback) -> bool;
  void stop();
  auto isRunning() const noexcept -> bool;

private:
  CommandCallback              callback_;
  std::unique_ptr<std::thread> serverThread_;
  std::atomic<bool>            shouldStop_;
  std::string                  socketPath_;

  int32_t serverFd_;
  bool    initialized_;

  auto initializeSocket() -> bool;
  void cleanupSocket() noexcept;
  void serverThreadFunction();
  void handleClient(int32_t clientFd);

  static void copySocketPath(std::span<char> destinationBuffer, const std::string& source) noexcept;
};

}  // namespace SnakeGame
