import sqlite3
from datetime import datetime
import threading


class GameDatabase:
    def __init__(self, database_file="game_logs.db"):
        self.conn = sqlite3.connect(database_file, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                client_id TEXT,
                player_id TEXT,
                bet_type TEXT,
                bet_size INTEGER,
                rolled_number INTEGER,
                result BOOLEAN,
                payout INTEGER
            )
        ''')
        self.conn.commit()

    def log_game(self, client_id, player_id, bet_type, bet_size, rolled_number, result, payout):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO game_logs (timestamp, client_id, player_id, bet_type, bet_size, rolled_number, result, payout)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, client_id, player_id, bet_type, bet_size, rolled_number, result, payout))
        self.conn.commit()

    def get_history_for_player(self, player_id):
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) AS total_games,
                   SUM(CAST(result AS INTEGER)) AS total_wins,
                   SUM(payout) AS total_payout
            FROM game_logs
            WHERE player_id = ?
        ''', (player_id,))

        result = cursor.fetchone()

        total_games = result[0]
        total_wins = result[1]
        total_losses = total_games - total_wins
        total_payout = result[2]

        return f"Total games:{total_games},W:{total_wins},L:{total_losses},P:{total_payout}"

    def insert_logs(self, logs):
        for log in logs:
            data = log.split(",")
            self.log_game(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

    def close_connection(self):
        self.conn.close()
