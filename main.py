import os
from portfolio_manager import add_position, buy_more_shares

while True:

    os.system("cls")

    print("=" * 60)
    print("                         HELIX")
    print("=" * 60)
    print("        Your Personal Investing Intelligence")
    print("=" * 60)

    print("\n1. View Portfolio")
    print("2. Add Position")
    print("3. Buy More Shares")
    print("4. Sell Shares")
    print("5. AI Analysis")
    print("6. Market News")
    print("7. Exit")

    choice = input("\nChoose an option: ")

    if choice == "1":
        os.system("python portfolio.py")
        input("\nPress Enter to return to the menu...")

    elif choice == "2":
        add_position()
        input("\nPress Enter to continue...")

    elif choice == "3":
        buy_more_shares()
        input("\nPress Enter to continue...")

    elif choice == "4":
        print("\nComing Soon!")
        input("\nPress Enter to continue...")

    elif choice == "5":
        print("\nComing Soon!")
        input("\nPress Enter to continue...")

    elif choice == "6":
        print("\nComing Soon!")
        input("\nPress Enter to continue...")

    elif choice == "7":
        print("\nThanks for using HELIX!")
        break

    else:
        print("\nInvalid option.")
        input("Press Enter...")
