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

/**
 * @brief Manages a UNIX domain socket server for receiving IPC commands.
 *
 * This class creates a non-blocking socket server that listens for incoming
 * connections and invokes a callback function when commands are received.
 */
class CommandSocket
{
public:
  /**
   * @brief Constructs a CommandSocket with the specified socket path.
   *
   * @param socketPath Path to the UNIX domain socket file (default: /tmp/snake_game.sock).
   */
  explicit CommandSocket(std::string socketPath = std::string{DEFAULT_SOCKET_PATH});
  ~CommandSocket();

  CommandSocket(const CommandSocket& other)                   = delete;
  CommandSocket(CommandSocket&& other)                        = delete;
  auto operator=(const CommandSocket& other) -> CommandSocket = delete;
  auto operator=(CommandSocket&& other) -> CommandSocket      = delete;

  /**
   * @brief Starts the socket server on a background thread.
   *
   * @param callback Function to invoke when a command is received.
   * @return true If server started successfully.
   * @return false If initialization failed.
   */
  auto start(CommandCallback callback) -> bool;

  /**
   * @brief Stops the socket server and joins the background thread.
   */
  void stop();

  /**
   * @brief Checks if the server is currently running.
   *
   * @return true If the server thread is active.
   * @return false Otherwise.
   */
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
