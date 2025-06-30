import backtrader as bt

class FuturesCommission(bt.CommInfoBase):
    """
    A commission and margin model for futures contracts.
    - Fixed commission per contract.
    - Contract multiplier.
    - Margin per contract.
    """

    params = (
        ('commission', 2.5),  # Per side commission in dollars
        ('mult', 1),          # Contract multiplier (e.g., 1000 for Crude)
        ('margin', 5000),     # Initial margin per contract
        ('commtype', bt.CommInfoBase.COMM_FIXED),  # Fixed commission per contract
        ('percabs', True)     # Commission is absolute dollars, not percentage
    )

    def getsize(self, price, cash):
        """
        Position size calculation based on margin requirement.
        """
        size = int(cash / self.p.margin)
        return size
