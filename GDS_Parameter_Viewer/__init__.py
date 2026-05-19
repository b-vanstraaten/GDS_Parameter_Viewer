__version__ = "0.1.1"

def __print_welcome_message():
    from colorama import init
    # <--- ensures ANSI codes are translated properly
    import random

    init(autoreset=True)

    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    authors = ['Barnaby van Straaten']
    supporters = ['QuTech TU Delft']
    random.shuffle(authors)
    random.shuffle(supporters)

    message = (
        f"\n{BOLD}{CYAN}GDS_Parameter_Viwer{RESET} version: {__version__}"
        f"\n{YELLOW}Authors:{RESET} {', '.join(authors)}"
        f"\n{YELLOW}Supported by:{RESET} {', '.join(supporters)}"
        f"\n{YELLOW}License:{RESET} GPL"
    )
    print(message)


__print_welcome_message()
