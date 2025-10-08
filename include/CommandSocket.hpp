#pragma once

#include "Types.hpp"

#include <atomic>
#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <thread>

namespace SnakeGame
{

using CommandCallback = std::function<void(IpcCommands)>;

inline constexpr std::string_view DEFAULT_SOCKET_PATH = "/tmp/snake_game.sock";

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

  [[nodiscard]] auto isRunning() const noexcept -> bool;

private:
  std::string     socketPath_;
  int             serverFd_;
  bool            initialized_;
  CommandCallback callback_;

  std::unique_ptr<std::thread> serverThread_;
  std::atomic<bool>            shouldStop_;

  auto initializeSocket() -> bool;

  void cleanupSocket() noexcept;
  void serverThreadFunction();
  void handleClient(int clientFd);
};

}  // namespace SnakeGame
