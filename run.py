from anicli import AnicliRuTui

if __name__ == '__main__':
    app = AnicliRuTui()

    try:
        app.run()
    finally:
        app.mpv_ipc_socket.terminate()
