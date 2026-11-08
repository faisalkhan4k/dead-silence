"""Test the configured ElevenLabs voice without starting microphone input."""
import sys
from breath_language import speak


def main():
    try:
        speak('Hello! This is your crewmate. Your ElevenLabs voice is ready.')
    except Exception as error:
        print('Voice test failed:', error)
        return 1
    print('Voice test finished. You should have heard the sample.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
