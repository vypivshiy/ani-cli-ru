import argparse

def main():
    parser = argparse.ArgumentParser(description="Rich Presence Script")

    parser.add_argument("-n", "--name", type=str, help="", required=True)
    parser.add_argument("-e", "--episode", type=str, help="", required=True)
    parser.add_argument("-em", "--episode_max", type=str, help="", required=True)
    parser.add_argument("-t", "--thumbnail", type=str, help="", required=True)

    args = parser.parse_args()

    from pypresence import Presence
    import time
    client_id = "1392818712511385652"
    RPC = Presence(client_id)
    RPC.connect()

    while True:
        RPC.update(
            state=str(args.name),
            large_image=str(args.thumbnail),
            details="Смотрит Аниме",
            party_size=[int(args.episode), int(args.episode)],
            buttons=[{"label": "Github Repository", "url": "https://github.com"}],
        )
        time.sleep(15)  # minimum 15 seconds

if __name__ == "__main__":
    main()