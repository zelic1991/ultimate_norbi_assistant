# Generated from spec
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--echo", default="ok")
    a = p.parse_args()
    print(a.echo)

if __name__ == "__main__":
    main()
