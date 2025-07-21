
import sys, argparse, logging
from license_validator.validator import validate

logging.basicConfig(level="INFO")

def main():
    parser = argparse.ArgumentParser(description="License validator CLI")
    parser.add_argument("license_file", help="Path to license.json")
    parser.add_argument("public_key", help="Customer public key")
    args = parser.parse_args()
    ok = validate(args.license_file, args.public_key)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
