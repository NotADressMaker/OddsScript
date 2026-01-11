#!/usr/bin/env python3
"""
Gambling Tax Calculator (US)

Calculate taxes on gambling winnings according to US tax law.
"""

import argparse
from typing import Dict


class GamblingTaxCalculator:
    """Calculate US gambling taxes"""

    # 2024 Federal tax brackets (single filer)
    TAX_BRACKETS_SINGLE = [
        (11600, 0.10),      # 10% up to $11,600
        (47150, 0.12),      # 12% up to $47,150
        (100525, 0.22),     # 22% up to $100,525
        (191950, 0.24),     # 24% up to $191,950
        (243725, 0.32),     # 32% up to $243,725
        (609350, 0.35),     # 35% up to $609,350
        (float('inf'), 0.37)  # 37% above
    ]

    # 2024 Federal tax brackets (married filing jointly)
    TAX_BRACKETS_MARRIED = [
        (23200, 0.10),
        (94300, 0.12),
        (201050, 0.22),
        (383900, 0.24),
        (487450, 0.32),
        (731200, 0.35),
        (float('inf'), 0.37)
    ]

    # Standard deduction 2024
    STANDARD_DEDUCTION_SINGLE = 14600
    STANDARD_DEDUCTION_MARRIED = 29200

    @staticmethod
    def calculate_federal_tax(
        gross_income: float,
        gambling_winnings: float,
        gambling_losses: float,
        filing_status: str = 'single'
    ) -> Dict:
        """
        Calculate federal tax with gambling income

        Args:
            gross_income: Total gross income (excluding gambling)
            gambling_winnings: Total gambling winnings
            gambling_losses: Total gambling losses (can only deduct up to winnings)
            filing_status: 'single' or 'married'

        Returns:
            Dictionary with tax calculations
        """
        # Select tax brackets
        if filing_status == 'married':
            brackets = GamblingTaxCalculator.TAX_BRACKETS_MARRIED
            std_deduction = GamblingTaxCalculator.STANDARD_DEDUCTION_MARRIED
        else:
            brackets = GamblingTaxCalculator.TAX_BRACKETS_SINGLE
            std_deduction = GamblingTaxCalculator.STANDARD_DEDUCTION_SINGLE

        # Calculate AGI
        # Gambling losses can only be deducted up to gambling winnings
        # and only if itemizing
        deductible_losses = min(gambling_losses, gambling_winnings)

        # Total income includes all gambling winnings
        total_income = gross_income + gambling_winnings

        # Scenario 1: Standard deduction (cannot deduct gambling losses)
        agi_standard = max(0, total_income - std_deduction)
        tax_standard = GamblingTaxCalculator._calculate_tax_from_brackets(
            agi_standard, brackets
        )

        # Scenario 2: Itemized deduction (can deduct gambling losses)
        # Assuming standard deduction is only other deduction
        itemized_total = std_deduction + deductible_losses
        agi_itemized = max(0, total_income - itemized_total)
        tax_itemized = GamblingTaxCalculator._calculate_tax_from_brackets(
            agi_itemized, brackets
        )

        # Choose better option
        if tax_itemized < tax_standard:
            recommended = 'itemized'
            tax_owed = tax_itemized
            agi = agi_itemized
            deductions = itemized_total
        else:
            recommended = 'standard'
            tax_owed = tax_standard
            agi = agi_standard
            deductions = std_deduction

        # Calculate effective tax rate
        effective_rate = (tax_owed / total_income * 100) if total_income > 0 else 0

        # Net gambling profit after taxes
        net_gambling_profit = gambling_winnings - gambling_losses - \
                             (tax_owed if recommended == 'itemized' else 0)

        return {
            'gross_income': gross_income,
            'gambling_winnings': gambling_winnings,
            'gambling_losses': gambling_losses,
            'deductible_losses': deductible_losses if recommended == 'itemized' else 0,
            'total_income': total_income,
            'agi': agi,
            'deductions': deductions,
            'taxable_income': agi,
            'federal_tax': tax_owed,
            'effective_rate': effective_rate,
            'recommended_filing': recommended,
            'tax_standard': tax_standard,
            'tax_itemized': tax_itemized,
            'net_gambling_profit': net_gambling_profit
        }

    @staticmethod
    def _calculate_tax_from_brackets(income: float, brackets: list) -> float:
        """Calculate tax using progressive brackets"""
        tax = 0
        previous_limit = 0

        for limit, rate in brackets:
            if income <= previous_limit:
                break

            taxable_in_bracket = min(income, limit) - previous_limit
            tax += taxable_in_bracket * rate

            previous_limit = limit

        return tax

    @staticmethod
    def calculate_withholding_requirements(winnings: float, odds: float = None) -> Dict:
        """
        Calculate if withholding is required

        Casinos must withhold 24% if:
        - Winnings are $5,000 or more, AND
        - Winnings are at least 300x the wager

        Args:
            winnings: Amount won
            odds: Odds (to calculate if 300x rule applies)

        Returns:
            Dictionary with withholding info
        """
        requires_withholding = False
        withholding_amount = 0
        withholding_rate = 0.24

        # Check $5,000 threshold
        if winnings >= 5000:
            # Check 300x rule if odds provided
            if odds is not None:
                if odds >= 300:
                    requires_withholding = True
            else:
                # Conservative: assume it might require withholding
                requires_withholding = True

        if requires_withholding:
            withholding_amount = winnings * withholding_rate

        return {
            'winnings': winnings,
            'requires_withholding': requires_withholding,
            'withholding_rate': withholding_rate * 100,
            'withholding_amount': withholding_amount,
            'net_after_withholding': winnings - withholding_amount
        }

    @staticmethod
    def calculate_quarterly_estimates(annual_gambling_profit: float, tax_bracket: float = 0.24) -> Dict:
        """
        Calculate quarterly estimated tax payments

        Args:
            annual_gambling_profit: Expected annual profit from gambling
            tax_bracket: Your marginal tax bracket

        Returns:
            Dictionary with quarterly payment info
        """
        annual_tax = annual_gambling_profit * tax_bracket
        quarterly_payment = annual_tax / 4

        # Payment deadlines
        deadlines = [
            "April 15",
            "June 15",
            "September 15",
            "January 15 (next year)"
        ]

        return {
            'annual_profit': annual_gambling_profit,
            'tax_bracket': tax_bracket * 100,
            'annual_tax': annual_tax,
            'quarterly_payment': quarterly_payment,
            'deadlines': deadlines
        }


def main():
    parser = argparse.ArgumentParser(
        description='US Gambling Tax Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s -i 75000 -w 25000 -l 18000 --status single

This calculates taxes for someone with:
  - $75,000 regular income
  - $25,000 gambling winnings
  - $18,000 gambling losses
  - Filing single

Note: This is for educational purposes. Consult a tax professional
for actual tax advice.
        """
    )

    parser.add_argument('-i', '--income', type=float, required=True,
                       help='Gross income (excluding gambling)')
    parser.add_argument('-w', '--winnings', type=float, required=True,
                       help='Total gambling winnings')
    parser.add_argument('-l', '--losses', type=float, default=0,
                       help='Total gambling losses')
    parser.add_argument('--status', choices=['single', 'married'],
                       default='single', help='Filing status')
    parser.add_argument('--state-tax', type=float, default=0,
                       help='State tax rate (as decimal, e.g., 0.05 for 5%%)')

    args = parser.parse_args()

    calc = GamblingTaxCalculator()

    # Calculate federal tax
    result = calc.calculate_federal_tax(
        args.income,
        args.winnings,
        args.losses,
        args.status
    )

    print(f"\n{'='*70}")
    print(f"US Gambling Tax Calculator")
    print(f"Filing Status: {args.status.title()}")
    print(f"{'='*70}")

    print(f"\nIncome Summary:")
    print(f"  Regular Income:      ${result['gross_income']:>12,.2f}")
    print(f"  Gambling Winnings:   ${result['gambling_winnings']:>12,.2f}")
    print(f"  Gambling Losses:     ${result['gambling_losses']:>12,.2f}")
    print(f"  Total Income:        ${result['total_income']:>12,.2f}")

    print(f"\nDeductions:")
    print(f"  Filing Method: {result['recommended_filing'].title()}")
    print(f"  Total Deductions:    ${result['deductions']:>12,.2f}")

    if result['recommended_filing'] == 'itemized':
        print(f"    Standard Deduction:    ${calc.STANDARD_DEDUCTION_SINGLE if args.status == 'single' else calc.STANDARD_DEDUCTION_MARRIED:>8,.2f}")
        print(f"    Gambling Losses:       ${result['deductible_losses']:>8,.2f}")

    print(f"\nTaxable Income:        ${result['taxable_income']:>12,.2f}")

    print(f"\nTax Calculation:")
    print(f"  Federal Tax:         ${result['federal_tax']:>12,.2f}")
    print(f"  Effective Tax Rate:  {result['effective_rate']:>12.2f}%")

    # State tax if provided
    if args.state_tax > 0:
        state_tax = result['taxable_income'] * args.state_tax
        total_tax = result['federal_tax'] + state_tax

        print(f"  State Tax ({args.state_tax*100:.1f}%):      ${state_tax:>12,.2f}")
        print(f"  Total Tax:           ${total_tax:>12,.2f}")
    else:
        total_tax = result['federal_tax']

    print(f"\nNet Gambling Result:")
    gambling_profit = result['gambling_winnings'] - result['gambling_losses']
    net_after_tax = gambling_profit - result['federal_tax'] + \
                   (result['gambling_losses'] if result['recommended_filing'] == 'standard' else 0)

    print(f"  Gross Profit:        ${gambling_profit:>12,.2f}")
    print(f"  Net After Tax:       ${result['net_gambling_profit']:>12,.2f}")

    # Filing comparison
    print(f"\nFiling Method Comparison:")
    print(f"  Standard Deduction:  ${result['tax_standard']:>12,.2f} tax")
    print(f"  Itemized Deduction:  ${result['tax_itemized']:>12,.2f} tax")
    savings = abs(result['tax_standard'] - result['tax_itemized'])
    print(f"  Tax Savings:         ${savings:>12,.2f}")

    # Withholding check for large wins
    if result['gambling_winnings'] >= 5000:
        print(f"\n⚠️  Winnings >= $5,000 may trigger withholding requirements")

    # Quarterly estimates
    if gambling_profit > 1000:
        print(f"\n💡 Consider making quarterly estimated tax payments")
        bracket = 0.24  # Assuming 24% bracket
        quarterly = calc.calculate_quarterly_estimates(gambling_profit, bracket)
        print(f"   Quarterly payment: ${quarterly['quarterly_payment']:.2f}")

    print(f"\n{'='*70}")
    print(f"DISCLAIMER: This is for educational purposes only.")
    print(f"Consult a qualified tax professional for tax advice.")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
