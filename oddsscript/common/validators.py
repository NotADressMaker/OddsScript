"""
Input validation utilities for all OddsScript tools.

Provides consistent validation with helpful error messages.
"""

from typing import Any, Union, Optional


class ValidationError(Exception):
    """Custom validation error with helpful messages"""
    pass


class Validators:
    """Common input validators for betting operations"""

    @staticmethod
    def validate_odds(odds: float, format: str = 'american') -> float:
        """
        Validate odds are in valid range

        Args:
            odds: Odds value
            format: 'american', 'decimal', or 'fractional'

        Returns:
            Validated odds

        Raises:
            ValidationError: If odds are invalid

        Examples:
            >>> Validators.validate_odds(-110)
            -110
            >>> Validators.validate_odds(-50)  # doctest: +SKIP
            ValidationError: Invalid American odds: -50
        """
        if format == 'american':
            # American odds must be less than -100 or greater than 100
            # (can't have odds between -100 and +100)
            if odds < -10000:
                raise ValidationError(
                    f"Invalid American odds: {odds} (too extreme, must be > -10000)"
                )
            elif odds > 10000:
                raise ValidationError(
                    f"Invalid American odds: {odds} (too extreme, must be < +10000)"
                )
            elif -100 < odds < 100:
                raise ValidationError(
                    f"Invalid American odds: {odds} (must be < -100 or > +100)"
                )
            return odds

        elif format == 'decimal':
            if odds < 1.01:
                raise ValidationError(
                    f"Invalid decimal odds: {odds} (must be >= 1.01)"
                )
            if odds > 1000:
                raise ValidationError(
                    f"Invalid decimal odds: {odds} (too extreme, must be < 1000)"
                )
            return odds

        else:
            raise ValidationError(f"Unknown odds format: {format}")

    @staticmethod
    def validate_probability(prob: float, name: str = "probability") -> float:
        """
        Validate probability is between 0 and 1

        Args:
            prob: Probability value
            name: Name for error message

        Returns:
            Validated probability

        Raises:
            ValidationError: If probability is out of range
        """
        if not isinstance(prob, (int, float)):
            raise ValidationError(
                f"Invalid {name}: {prob} (must be a number)"
            )

        if prob < 0 or prob > 1:
            raise ValidationError(
                f"Invalid {name}: {prob} (must be between 0 and 1)"
            )

        return prob

    @staticmethod
    def validate_stake(stake: float, min_stake: float = 0.01) -> float:
        """
        Validate stake is positive and reasonable

        Args:
            stake: Stake amount
            min_stake: Minimum allowed stake

        Returns:
            Validated stake

        Raises:
            ValidationError: If stake is invalid
        """
        if not isinstance(stake, (int, float)):
            raise ValidationError(
                f"Invalid stake: {stake} (must be a number)"
            )

        if stake <= 0:
            raise ValidationError(
                f"Invalid stake: {stake} (must be positive)"
            )

        if stake < min_stake:
            raise ValidationError(
                f"Invalid stake: {stake} (must be at least {min_stake})"
            )

        return stake

    @staticmethod
    def validate_bankroll(bankroll: float, min_bankroll: float = 1.0) -> float:
        """
        Validate bankroll is positive and reasonable

        Args:
            bankroll: Bankroll amount
            min_bankroll: Minimum allowed bankroll

        Returns:
            Validated bankroll

        Raises:
            ValidationError: If bankroll is invalid
        """
        if not isinstance(bankroll, (int, float)):
            raise ValidationError(
                f"Invalid bankroll: {bankroll} (must be a number)"
            )

        if bankroll <= 0:
            raise ValidationError(
                f"Invalid bankroll: {bankroll} (must be positive)"
            )

        if bankroll < min_bankroll:
            raise ValidationError(
                f"Invalid bankroll: {bankroll} (must be at least {min_bankroll})"
            )

        return bankroll

    @staticmethod
    def validate_kelly_fraction(fraction: float) -> float:
        """
        Validate Kelly fraction

        Args:
            fraction: Kelly fraction (typically 0.1 to 1.0)

        Returns:
            Validated fraction

        Raises:
            ValidationError: If fraction is invalid
        """
        if not isinstance(fraction, (int, float)):
            raise ValidationError(
                f"Invalid Kelly fraction: {fraction} (must be a number)"
            )

        if fraction <= 0:
            raise ValidationError(
                f"Invalid Kelly fraction: {fraction} (must be positive)"
            )

        if fraction > 1:
            raise ValidationError(
                f"Invalid Kelly fraction: {fraction} (must be <= 1.0)"
            )

        # Warning for full Kelly
        if fraction > 0.5:
            import warnings
            warnings.warn(
                f"Kelly fraction {fraction} is aggressive. "
                "Consider using 0.25 (quarter Kelly) for safer bankroll management.",
                UserWarning
            )

        return fraction

    @staticmethod
    def validate_percentage(pct: float, name: str = "percentage") -> float:
        """
        Validate percentage (0-100)

        Args:
            pct: Percentage value
            name: Name for error message

        Returns:
            Validated percentage

        Raises:
            ValidationError: If percentage is out of range
        """
        if not isinstance(pct, (int, float)):
            raise ValidationError(
                f"Invalid {name}: {pct} (must be a number)"
            )

        if pct < 0 or pct > 100:
            raise ValidationError(
                f"Invalid {name}: {pct} (must be between 0 and 100)"
            )

        return pct

    @staticmethod
    def validate_sport(sport: str, allowed_sports: Optional[list] = None) -> str:
        """
        Validate sport name

        Args:
            sport: Sport abbreviation
            allowed_sports: Optional list of allowed sports

        Returns:
            Validated sport (lowercase)

        Raises:
            ValidationError: If sport is invalid
        """
        if not isinstance(sport, str):
            raise ValidationError(
                f"Invalid sport: {sport} (must be a string)"
            )

        sport = sport.lower().strip()

        if allowed_sports is not None:
            allowed = [s.lower() for s in allowed_sports]
            if sport not in allowed:
                raise ValidationError(
                    f"Invalid sport: {sport} (must be one of {allowed_sports})"
                )

        return sport

    @staticmethod
    def validate_date(date_str: str) -> str:
        """
        Validate date format (YYYY-MM-DD)

        Args:
            date_str: Date string

        Returns:
            Validated date string

        Raises:
            ValidationError: If date format is invalid
        """
        from datetime import datetime

        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            raise ValidationError(
                f"Invalid date format: {date_str} (must be YYYY-MM-DD)"
            )

    @staticmethod
    def validate_result(result: str) -> str:
        """
        Validate bet result

        Args:
            result: Result string

        Returns:
            Validated result (lowercase)

        Raises:
            ValidationError: If result is invalid
        """
        valid_results = ['win', 'loss', 'push', 'void', 'pending']
        result = result.lower().strip()

        if result not in valid_results:
            raise ValidationError(
                f"Invalid result: {result} (must be one of {valid_results})"
            )

        return result

    @staticmethod
    def validate_positive_int(value: int, name: str = "value") -> int:
        """
        Validate positive integer

        Args:
            value: Integer value
            name: Name for error message

        Returns:
            Validated integer

        Raises:
            ValidationError: If not a positive integer
        """
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError(
                f"Invalid {name}: {value} (must be an integer)"
            )

        if value <= 0:
            raise ValidationError(
                f"Invalid {name}: {value} (must be positive)"
            )

        return value

    @staticmethod
    def validate_correlation(correlation: float) -> float:
        """
        Validate correlation coefficient

        Args:
            correlation: Correlation value

        Returns:
            Validated correlation

        Raises:
            ValidationError: If correlation is out of range
        """
        if not isinstance(correlation, (int, float)):
            raise ValidationError(
                f"Invalid correlation: {correlation} (must be a number)"
            )

        if correlation < -1 or correlation > 1:
            raise ValidationError(
                f"Invalid correlation: {correlation} (must be between -1 and 1)"
            )

        return correlation

    @staticmethod
    def validate_line(line: float) -> float:
        """
        Validate betting line (spread or total)

        Args:
            line: Line value

        Returns:
            Validated line

        Raises:
            ValidationError: If line is invalid
        """
        if not isinstance(line, (int, float)):
            raise ValidationError(
                f"Invalid line: {line} (must be a number)"
            )

        # Lines typically range from -50 to +50 for spreads
        # and 0 to 300 for totals
        if abs(line) > 500:
            raise ValidationError(
                f"Invalid line: {line} (too extreme, must be between -500 and +500)"
            )

        return line


# Convenience functions
validate_odds = Validators.validate_odds
validate_probability = Validators.validate_probability
validate_stake = Validators.validate_stake
validate_bankroll = Validators.validate_bankroll
validate_kelly_fraction = Validators.validate_kelly_fraction
