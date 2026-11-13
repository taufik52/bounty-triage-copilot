"""Example drafts shipped with the app for the demo (one strong, one weak)."""

SAMPLES = [
    {
        "id": "strong",
        "label": "Strong draft — reentrancy in Vault.withdraw",
        "program": "Example DeFi Vault",
        "title": "Reentrancy in Vault.withdraw allows draining user funds (High)",
        "draft": """## Summary
Vault.withdraw sends ETH to the caller before updating the caller's balance, so a malicious contract can re-enter withdraw in its receive() and drain the vault.

## Severity: High
An attacker can steal funds belonging to other users. The vault holds user deposits, so impact is direct loss of funds. Precondition: attacker must be a depositor with any balance.

## Proof of Concept
Vulnerable contract: 0x1234567890abcdef1234567890abcdef12345678

Attacker contract calls:
```
function attack() external {
    vault.withdraw(1 ether);
}
receive() external payable {
    if (address(vault).balance >= 1 ether) {
        vault.withdraw(1 ether);
    }
}
```
Reproduce with Foundry:
```
forge test --match-test testReentrancyDrain -vvv
```

## Steps to Reproduce
1. Deploy Vault and deposit 10 ether from two honest users.
2. Deploy the attacker contract and deposit 1 ether.
3. Call attack() from the attacker contract.
4. Observe the vault balance drop to zero while the attacker balance grows.
5. Expected behaviour: withdraw updates balances before the external call. Actual behaviour: the vault is drained.

## Recommended Fix
Follow checks-effects-interactions: update balances before the external call, and add a reentrancy guard.
""",
    },
    {
        "id": "weak",
        "label": "Weak draft — vague access-control claim",
        "program": "Example DeFi Vault",
        "title": "bug in contract",
        "draft": """I found a bug. Sometimes the admin function can maybe be called by anyone, I think. It might be a problem. Not sure how to reproduce it exactly, but you should check it. This is probably critical.
""",
    },
]
