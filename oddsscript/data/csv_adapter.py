"""
CSV storage backend for OddsScript.

Stores data in CSV files for simplicity and portability.
"""

import csv
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from oddsscript.data.storage import StorageBackend


class CSVStorage(StorageBackend):
    """CSV-based storage implementation"""

    def __init__(self, data_dir: Path):
        """
        Initialize CSV storage

        Args:
            data_dir: Directory for CSV files
        """
        if isinstance(data_dir, str):
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.bets_file = data_dir / 'bets.csv'
        self.lines_file = data_dir / 'lines.csv'

        # Create files with headers if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Create CSV files with headers if they don't exist"""
        # Bets file
        if not self.bets_file.exists():
            with open(self.bets_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'id', 'date', 'sport', 'description', 'odds', 'stake',
                    'result', 'profit', 'clv', 'notes', 'created_at'
                ])
                writer.writeheader()

        # Lines file
        if not self.lines_file.exists():
            with open(self.lines_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'id', 'game_id', 'timestamp', 'sportsbook', 'bet_type',
                    'line', 'odds', 'created_at'
                ])
                writer.writeheader()

    def save_bet(self, bet: Dict[str, Any]) -> str:
        """Save bet and return ID"""
        bet_id = str(uuid.uuid4())

        # Add metadata
        bet_row = {
            'id': bet_id,
            'date': bet.get('date', ''),
            'sport': bet.get('sport', ''),
            'description': bet.get('description', ''),
            'odds': bet.get('odds', ''),
            'stake': bet.get('stake', ''),
            'result': bet.get('result', ''),
            'profit': bet.get('profit', ''),
            'clv': bet.get('clv', ''),
            'notes': bet.get('notes', ''),
            'created_at': datetime.now().isoformat()
        }

        # Append to file
        with open(self.bets_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=bet_row.keys())
            writer.writerow(bet_row)

        return bet_id

    def get_bet(self, bet_id: str) -> Optional[Dict[str, Any]]:
        """Get bet by ID"""
        with open(self.bets_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['id'] == bet_id:
                    return self._parse_bet_row(row)
        return None

    def update_bet(self, bet_id: str, updates: Dict[str, Any]) -> bool:
        """Update bet with new data"""
        rows = []
        found = False

        # Read all rows
        with open(self.bets_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['id'] == bet_id:
                    # Update fields
                    for key, value in updates.items():
                        if key in row:
                            row[key] = value
                    found = True
                rows.append(row)

        if not found:
            return False

        # Write back
        if rows:
            with open(self.bets_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return True

    def list_bets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List bets with optional filters"""
        bets = []

        with open(self.bets_file, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Apply filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key in row and row[key] != str(value):
                            match = False
                            break
                    if not match:
                        continue

                bets.append(self._parse_bet_row(row))

        # Apply offset and limit
        if offset:
            bets = bets[offset:]
        if limit:
            bets = bets[:limit]

        return bets

    def delete_bet(self, bet_id: str) -> bool:
        """Delete bet"""
        rows = []
        found = False

        # Read all rows except the one to delete
        with open(self.bets_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['id'] == bet_id:
                    found = True
                    continue
                rows.append(row)

        if not found:
            return False

        # Write back
        if rows:
            with open(self.bets_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return True

    def save_line_movement(self, line: Dict[str, Any]) -> str:
        """Save line movement data"""
        line_id = str(uuid.uuid4())

        line_row = {
            'id': line_id,
            'game_id': line.get('game_id', ''),
            'timestamp': line.get('timestamp', datetime.now().isoformat()),
            'sportsbook': line.get('sportsbook', ''),
            'bet_type': line.get('bet_type', ''),
            'line': line.get('line', ''),
            'odds': line.get('odds', ''),
            'created_at': datetime.now().isoformat()
        }

        # Append to file
        with open(self.lines_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=line_row.keys())
            writer.writerow(line_row)

        return line_id

    def get_line_history(
        self,
        game_id: str,
        sportsbook: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get line movement history for a game"""
        lines = []

        with open(self.lines_file, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Filter by game_id
                if row['game_id'] != game_id:
                    continue

                # Filter by sportsbook
                if sportsbook and row['sportsbook'] != sportsbook:
                    continue

                # Parse timestamp
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                except:
                    continue

                # Filter by time range
                if start_time and ts < start_time:
                    continue
                if end_time and ts > end_time:
                    continue

                lines.append(self._parse_line_row(row))

        # Sort by timestamp
        lines.sort(key=lambda x: x['timestamp'])

        return lines

    def get_stats(
        self,
        sport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get betting statistics"""
        filters = {}
        if sport:
            filters['sport'] = sport

        all_bets = self.list_bets(filters=filters)

        # Filter by date
        if start_date or end_date:
            filtered_bets = []
            for bet in all_bets:
                bet_date = bet.get('date', '')
                if start_date and bet_date < start_date:
                    continue
                if end_date and bet_date > end_date:
                    continue
                filtered_bets.append(bet)
            all_bets = filtered_bets

        # Calculate stats
        total_bets = len(all_bets)
        settled = [b for b in all_bets if b.get('result')]

        wins = len([b for b in settled if b.get('result') == 'win'])
        losses = len([b for b in settled if b.get('result') == 'loss'])
        pushes = len([b for b in settled if b.get('result') == 'push'])

        total_profit = sum(float(b.get('profit', 0) or 0) for b in settled)
        total_staked = sum(float(b.get('stake', 0) or 0) for b in settled)

        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
        win_rate = (wins / len(settled) * 100) if settled else 0

        # CLV stats
        bets_with_clv = [b for b in settled if b.get('clv')]
        avg_clv = sum(float(b.get('clv', 0)) for b in bets_with_clv) / len(bets_with_clv) if bets_with_clv else 0

        return {
            'total_bets': total_bets,
            'settled': len(settled),
            'pending': total_bets - len(settled),
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_staked': total_staked,
            'roi': roi,
            'avg_clv': avg_clv,
            'sport': sport,
            'start_date': start_date,
            'end_date': end_date
        }

    def clear_all_data(self) -> bool:
        """Clear all data (USE WITH CAUTION!)"""
        # Reinitialize files (clears data)
        self._initialize_files()
        return True

    @staticmethod
    def _parse_bet_row(row: Dict[str, str]) -> Dict[str, Any]:
        """Parse CSV row into bet dictionary with proper types"""
        return {
            'id': row['id'],
            'date': row['date'],
            'sport': row['sport'],
            'description': row['description'],
            'odds': float(row['odds']) if row['odds'] else None,
            'stake': float(row['stake']) if row['stake'] else None,
            'result': row['result'] if row['result'] else None,
            'profit': float(row['profit']) if row['profit'] else None,
            'clv': float(row['clv']) if row['clv'] else None,
            'notes': row['notes'],
            'created_at': row['created_at']
        }

    @staticmethod
    def _parse_line_row(row: Dict[str, str]) -> Dict[str, Any]:
        """Parse CSV row into line movement dictionary with proper types"""
        return {
            'id': row['id'],
            'game_id': row['game_id'],
            'timestamp': row['timestamp'],
            'sportsbook': row['sportsbook'],
            'bet_type': row['bet_type'],
            'line': float(row['line']) if row['line'] else None,
            'odds': float(row['odds']) if row['odds'] else None,
            'created_at': row['created_at']
        }
