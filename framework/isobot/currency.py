import json
import discord
import datetime

class Colors:
    """Contains general stdout colors."""
    cyan = '\033[96m'
    red = '\033[91m'
    green = '\033[92m'
    end = '\033[0m'

class CurrencyAPI(Colors):
    """The isobot API used for managing currency.
    
    Valid commands:
    - add(user, amount)
    - remove(user, amount)
    - reset(user)
    - deposit(user, amount)
    - withdraw(user, amount)
    - wallet(user)
    - bank(user)"""

    def __init__(self, db_path: str, log_path: str):
        self.db_path = db_path
        self.log_path = log_path
        print(f"[Framework/Loader] {Colors.green}CurrencyAPI initialized.{Colors.end}")
    
    def get_time(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def add(self, user: discord.User, amount: int) -> int:
        """Adds balance to the specified user."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        currency["wallet"][str(user)] += int(amount)
        with open(self.db_path, 'w+') as f: json.dump(currency, f, indent=4)
        with open(self.log_path, 'a') as f:
            f.write(f'{self.get_time()} framework.isobot.currency User({user}): Added {amount} coins to wallet\n')
            f.close()
        return 0

    def remove(self, user: discord.User, amount: int) -> int:
        """Removes balance from the specified user."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        currency["wallet"][str(user)] -= int(amount)
        with open(self.db_path, 'w+') as f: json.dump(currency, f, indent=4)
        with open(self.log_path, 'a') as f:
            f.write(f'{self.get_time()} framework.isobot.currency User({user}): Removed {amount} coins from wallet\n')
            f.close()
        return 0

    def reset(self, user: discord.User) -> int:
        """Resets the specified user's balance."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        currency["wallet"][str(user)] = 0
        currency["bank"][str(user)] = 0
        with open(self.db_path, 'w+') as f: json.dump(currency, f, indent=4)
        print(f"[Framework/CurrencyAPI] Currency data for \"{user}\" has been wiped")
        with open(self.log_path, 'a') as f:
            f.write(f'{self.get_time()} framework.isobot.currency User({user}): Wiped all currency data\n')
            f.close()
        return 0

    def deposit(self, user: discord.User, amount: int) -> int:
        """Moves a specified amount of coins to the user's bank."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        currency["bank"][str(user)] += int(amount)
        currency["wallet"][str(user)] -= int(amount)
        with open(self.db_path, 'w+') as f: json.dump(currency, f, indent=4)
        print(f"[Framework/CurrencyAPI] Moved {amount} coins to bank. User: {user} [{user}]")
        with open(self.log_path, 'a') as f:
            f.write(f'{self.get_time()} framework.isobot.currency User({user}): Moved {amount} coins from wallet to bank\n')
            f.close()
        return 0

    def withdraw(self, user: discord.User, amount: int) -> int:
        """Moves a specified amount of coins to the user's wallet."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        currency["wallet"][str(user)] += int(amount)
        currency["bank"][str(user)] -= int(amount)
        with open(self.db_path, 'w+') as f: json.dump(currency, f, indent=4)
        print(f"[Framework/CurrencyAPI] Moved {amount} coins to wallet. User: {user} [{user}]")
        with open(self.log_path, 'a') as f:
            f.write(f'{self.get_time()} framework.isobot.currency User({user}): Moved {amount} coins from bank to wallet\n')
            f.close()
        return 0

    def wallet(self, user: discord.User) -> int:
        """Returns the amount of coins in the user's wallet."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        return int(currency["wallet"][str(user)])

    def bank(self, user: discord.User) -> int:
        """Returns the amount of coins in the user's bank account."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        return int(currency["bank"][str(user)])
    
    def net_worth(self, user: discord.User) -> int:
        """Returns the net-worth of the user."""
        with open(self.db_path, 'r') as f: currency = json.load(f)
        nw = int(currency["wallet"][str(user)]) + int(currency["bank"][str(user)]) 
        return nw
