#!/usr/bin/env python3
"""
Test script for Phase 1 foundation components.

Tests:
- oddsscript.common (odds, kelly, validators)
- oddsscript.config (configuration system)
- oddsscript.data (storage abstraction)
- oddsscript.core (language files)
"""

import sys
import os

# Add oddsscript to path
sys.path.insert(0, '/home/user/programminglangauage')

def test_odds_conversion():
    """Test odds conversion utilities"""
    print("\n" + "="*80)
    print("Testing Odds Conversion Utilities")
    print("="*80)

    from sportsbetlang.common.odds import (
        american_to_decimal,
        decimal_to_american,
        implied_probability,
        remove_vig,
        calculate_vig
    )

    # Test American to Decimal
    decimal = american_to_decimal(-110)
    print(f"✓ American to Decimal: -110 → {decimal}")
    assert abs(float(decimal) - 1.9091) < 0.001

    decimal = american_to_decimal(150)
    print(f"✓ American to Decimal: +150 → {decimal}")
    assert abs(float(decimal) - 2.5) < 0.001

    # Test Decimal to American
    american = decimal_to_american(1.91)
    print(f"✓ Decimal to American: 1.91 → {american:.2f}")
    assert abs(american - (-110)) < 2

    # Test Implied Probability
    prob = implied_probability(-110)
    print(f"✓ Implied Probability: -110 → {prob*100:.2f}%")
    assert abs(prob - 0.5238) < 0.001

    # Test Vig Calculation
    vig = calculate_vig(0.5238, 0.5238)
    print(f"✓ Vig Calculation: {vig:.2f}%")
    assert abs(vig - 4.76) < 0.1

    # Test Vig Removal
    fair1, fair2 = remove_vig(0.5238, 0.5238)
    print(f"✓ Vig Removal: ({fair1:.4f}, {fair2:.4f})")
    assert abs(fair1 - 0.5) < 0.001
    assert abs(fair2 - 0.5) < 0.001

    print("\n✅ All odds conversion tests passed!")


def test_kelly_criterion():
    """Test Kelly Criterion calculations"""
    print("\n" + "="*80)
    print("Testing Kelly Criterion Utilities")
    print("="*80)

    from sportsbetlang.common.kelly import calculate_kelly

    # Test basic Kelly
    result = calculate_kelly(
        odds=-110,
        true_prob=0.55,
        kelly_fraction=0.25,
        bankroll=1000
    )

    print(f"✓ Kelly Calculation:")
    print(f"  Odds: -110")
    print(f"  True Prob: 55%")
    print(f"  Kelly Fraction: 0.25")
    print(f"  Bankroll: $1000")
    print(f"  → Stake: ${result['stake']:.2f}")
    print(f"  → Edge: {result['edge']*100:+.2f}%")
    print(f"  → EV: {result['ev']*100:+.2f}%")

    assert result['stake'] > 0
    assert result['edge'] > 0
    assert result['recommended'] == 'BET'

    # Test no-bet scenario
    result = calculate_kelly(
        odds=-110,
        true_prob=0.45,  # Negative edge
        kelly_fraction=0.25,
        bankroll=1000
    )

    print(f"\n✓ No-Bet Scenario:")
    print(f"  True Prob: 45% (below market)")
    print(f"  → Recommendation: {result['recommended']}")

    assert result['recommended'] == 'NO BET'

    print("\n✅ All Kelly Criterion tests passed!")


def test_validators():
    """Test input validation"""
    print("\n" + "="*80)
    print("Testing Input Validators")
    print("="*80)

    from sportsbetlang.common.validators import (
        Validators,
        ValidationError
    )

    # Test valid odds
    try:
        Validators.validate_odds(-110)
        print("✓ Valid American odds (-110) accepted")
    except ValidationError as e:
        print(f"✗ Failed: {e}")
        raise

    # Test invalid odds
    try:
        Validators.validate_odds(-50)
        print("✗ Invalid odds (-50) should have been rejected")
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        print("✓ Invalid American odds (-50) correctly rejected")

    # Test probability validation
    try:
        Validators.validate_probability(0.55)
        print("✓ Valid probability (0.55) accepted")
    except ValidationError as e:
        print(f"✗ Failed: {e}")
        raise

    # Test invalid probability
    try:
        Validators.validate_probability(1.5)
        print("✗ Invalid probability (1.5) should have been rejected")
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        print("✓ Invalid probability (1.5) correctly rejected")

    # Test bankroll validation
    try:
        Validators.validate_bankroll(1000)
        print("✓ Valid bankroll (1000) accepted")
    except ValidationError as e:
        print(f"✗ Failed: {e}")
        raise

    # Test Kelly fraction validation
    try:
        Validators.validate_kelly_fraction(0.25)
        print("✓ Valid Kelly fraction (0.25) accepted")
    except ValidationError as e:
        print(f"✗ Failed: {e}")
        raise

    print("\n✅ All validator tests passed!")


def test_configuration():
    """Test configuration system"""
    print("\n" + "="*80)
    print("Testing Configuration System")
    print("="*80)

    from sportsbetlang.config import get_config, set_config, SportsBetLangConfig

    # Get default config
    config = get_config()
    print(f"✓ Default configuration loaded")
    print(f"  Kelly Fraction: {config.kelly_fraction}")
    print(f"  Storage Backend: {config.storage_backend}")
    print(f"  Data Directory: {config.data_directory}")
    print(f"  Enable Cache: {config.enable_cache}")
    print(f"  Max Workers: {config.max_workers}")

    # Test custom config
    custom_config = SportsBetLangConfig(
        kelly_fraction=0.5,
        storage_backend='sqlite',
        enable_multiprocessing=False
    )

    print(f"\n✓ Custom configuration created")
    print(f"  Kelly Fraction: {custom_config.kelly_fraction}")
    print(f"  Storage Backend: {custom_config.storage_backend}")
    print(f"  Enable Multiprocessing: {custom_config.enable_multiprocessing}")

    # Test config methods
    assert custom_config.get('kelly_fraction') == 0.5
    custom_config.set('kelly_fraction', 0.25)
    assert custom_config.get('kelly_fraction') == 0.25
    print(f"✓ Config get/set methods work correctly")

    print("\n✅ All configuration tests passed!")


def test_storage_csv():
    """Test CSV storage backend"""
    print("\n" + "="*80)
    print("Testing CSV Storage Backend")
    print("="*80)

    from sportsbetlang.data import create_storage
    from pathlib import Path
    import tempfile
    import shutil

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create CSV storage
        storage = create_storage('csv', data_dir=temp_dir)
        print(f"✓ CSV storage created in {temp_dir}")

        # Save a bet
        bet_id = storage.save_bet({
            'date': '2024-01-15',
            'sport': 'nfl',
            'description': 'Chiefs -3',
            'odds': -110,
            'stake': 110,
            'notes': 'Test bet'
        })
        print(f"✓ Bet saved with ID: {bet_id}")

        # Retrieve the bet
        bet = storage.get_bet(bet_id)
        assert bet is not None
        assert bet['sport'] == 'nfl'
        assert bet['description'] == 'Chiefs -3'
        print(f"✓ Bet retrieved successfully")

        # Update the bet
        success = storage.update_bet(bet_id, {
            'result': 'win',
            'profit': 100
        })
        assert success
        print(f"✓ Bet updated successfully")

        # Verify update
        bet = storage.get_bet(bet_id)
        assert bet['result'] == 'win'
        assert float(bet['profit']) == 100
        print(f"✓ Update verified")

        # List bets
        all_bets = storage.list_bets()
        assert len(all_bets) == 1
        print(f"✓ List bets: found {len(all_bets)} bet(s)")

        # Get stats
        stats = storage.get_stats()
        print(f"✓ Stats calculated:")
        print(f"  Total Bets: {stats['total_bets']}")
        print(f"  Wins: {stats['wins']}")
        print(f"  ROI: {stats['roi']:.2f}%")

        # Save line movement
        line_id = storage.save_line_movement({
            'game_id': 'game123',
            'sportsbook': 'pinnacle',
            'bet_type': 'spread',
            'line': -3.0,
            'odds': -110
        })
        print(f"✓ Line movement saved with ID: {line_id}")

        # Get line history
        history = storage.get_line_history('game123')
        assert len(history) == 1
        print(f"✓ Line history retrieved: {len(history)} record(s)")

        print("\n✅ All CSV storage tests passed!")

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_storage_sqlite():
    """Test SQLite storage backend"""
    print("\n" + "="*80)
    print("Testing SQLite Storage Backend")
    print("="*80)

    from sportsbetlang.data import create_storage
    from pathlib import Path
    import tempfile
    import shutil

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create SQLite storage
        db_path = temp_dir / 'test.db'
        storage = create_storage('sqlite', db_path=db_path)
        print(f"✓ SQLite storage created at {db_path}")

        # Save a bet
        bet_id = storage.save_bet({
            'date': '2024-01-15',
            'sport': 'nba',
            'description': 'Lakers ML',
            'odds': -150,
            'stake': 150
        })
        print(f"✓ Bet saved with ID: {bet_id}")

        # Retrieve the bet
        bet = storage.get_bet(bet_id)
        assert bet is not None
        assert bet['sport'] == 'nba'
        print(f"✓ Bet retrieved successfully")

        # Update the bet
        success = storage.update_bet(bet_id, {
            'result': 'loss',
            'profit': -150
        })
        assert success
        print(f"✓ Bet updated successfully")

        # List bets
        all_bets = storage.list_bets()
        assert len(all_bets) == 1
        print(f"✓ List bets: found {len(all_bets)} bet(s)")

        # Filter bets
        nba_bets = storage.list_bets(filters={'sport': 'nba'})
        assert len(nba_bets) == 1
        print(f"✓ Filter by sport: found {len(nba_bets)} NBA bet(s)")

        # Get stats
        stats = storage.get_stats(sport='nba')
        print(f"✓ Stats calculated:")
        print(f"  Total Bets: {stats['total_bets']}")
        print(f"  Losses: {stats['losses']}")
        print(f"  Total Profit: ${stats['total_profit']:.2f}")

        # Close connection
        storage.close()
        print(f"✓ Database connection closed")

        print("\n✅ All SQLite storage tests passed!")

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_package_imports():
    """Test that all packages import correctly"""
    print("\n" + "="*80)
    print("Testing Package Imports")
    print("="*80)

    # Test main package
    import sportsbetlang
    print(f"✓ oddsscript imported")
    print(f"  Version: {oddsscript.__version__}")

    # Test common
    from oddsscript import common
    print(f"✓ oddsscript.common imported")

    # Test config
    from oddsscript import config
    print(f"✓ oddsscript.config imported")

    # Test data
    from oddsscript import data
    print(f"✓ oddsscript.data imported")

    # Test core
    from oddsscript import core
    print(f"✓ oddsscript.core imported")

    # Test submodules
    from oddsscript import analytics, strategies, tools, api, cli
    print(f"✓ All submodules imported")

    print("\n✅ All package import tests passed!")


def main():
    """Run all tests"""
    print("\n" + "🚀" * 40)
    print("PHASE 1 FOUNDATION TESTS")
    print("🚀" * 40)

    tests = [
        ("Package Imports", test_package_imports),
        ("Odds Conversion", test_odds_conversion),
        ("Kelly Criterion", test_kelly_criterion),
        ("Validators", test_validators),
        ("Configuration", test_configuration),
        ("CSV Storage", test_storage_csv),
        ("SQLite Storage", test_storage_sqlite),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} FAILED:")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Phase 1 foundation is solid!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
