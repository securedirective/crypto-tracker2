import pytz
from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from database import engine

Base = declarative_base()

local_time_zone = pytz.timezone("America/New_York")


class ValidationError(Exception):
    pass


class Currency(Base):
    __tablename__ = 'currency'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    derivation_path = Column(String(100), nullable=True)
    smallest_unit = Column(String(20), nullable=False)
    digits_after_decimal = Column(Integer, nullable=False)
    usd_per_large = Column(Float, nullable=True)
    notes = Column(String(500), nullable=True)
    url_public_website = Column(String(500), nullable=True)
    url_source_code = Column(String(500), nullable=True)
    url_market_value = Column(String(500), nullable=True)
    url_block_info = Column(String(500), nullable=True)
    url_tx_info = Column(String(500), nullable=True)
    url_addr_info = Column(String(500), nullable=True)

    def format_large(self, small_amount):
        fmt = "{} {:." + str(self.digits_after_decimal) + "f}"
        return fmt.format(self.symbol, small_amount / (10**self.digits_after_decimal))
        # dsh -0.02460000

    def format_small(self, small_amount):
        fmt = "{} {:<3}"
        return fmt.format(small_amount, self.smallest_unit)
        # -2460000 sat

    def __str__(self):
        return "Currency #%s" % self.id


class Identity(Base):
    __tablename__ = 'identity'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    notes = Column(String(500), nullable=True)

    def __str__(self):
        return "Ident #%s" % self.id


class DeterministicSeed(Base):
    __tablename__ = 'seed'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    paper_local = Column(String(500), nullable=True)
    paper_offsite_1 = Column(String(500), nullable=True)
    paper_offsite_2 = Column(String(500), nullable=True)
    level_of_trust = Column(String(500), nullable=True)
    notes = Column(String(500), nullable=True)
    identity = Column(ForeignKey('identity.id', onupdate='CASCADE'), nullable=False)

    def __str__(self):
        return "Seed #%s" % self.id


class Wallet(Base):
    __tablename__ = 'wallet'

    id = Column(Integer, primary_key=True)
    seed = Column(ForeignKey('seed.id', onupdate='CASCADE'), nullable=False)
    currency = Column(ForeignKey('currency.id', onupdate='CASCADE'), nullable=False)
    derivation = Column(String(100), nullable=True)
    passphrase = Column(Integer, nullable=True)
    public_key = Column(String(500), nullable=True)

    def __str__(self):
        return "Wallet #%s" % self.id

    def str_short(self):
        return "#%s(%s)" % (self.id, self.currency.symbol)

    _str_long = None

    def str_long(self):
        if self._str_long:
            return self._str_long
        else:
            self._str_long = "%s > %s > %s (%s)" % (self.seed.identity.name, self.seed.name, self.currency.symbol, self.currency.name)
            if self.passphrase:
                self._str_long += (" > Pw%s" % self.passphrase)
            return self._str_long


class Transaction(Base):
    __tablename__ = 'transaction'
    __table_args__ = (
        # Database constraints will ensure that every wallet reference is accompanied by an amount
        # It also verifies the +/- of the amount column
        CheckConstraint('(from_wallet is null and from_amount is null) or (from_wallet is not null and from_amount < 0)', name='check_from'),
        CheckConstraint('(to_wallet is null and to_amount is null) or (to_wallet is not null and to_amount > 0)', name='check_to'),
        CheckConstraint('(fee_wallet is null and fee_amount is null) or (fee_wallet is not null and fee_amount < 0)', name='check_fee'),
    )

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    trans_type = Column(String(100), nullable=False)
    from_wallet = Column(ForeignKey('wallet.id', link_to_name='transaction_from', onupdate='CASCADE'), nullable=True)
    to_wallet = Column(ForeignKey('wallet.id', link_to_name='transaction_to', onupdate='CASCADE'), nullable=True)
    fee_wallet = Column(ForeignKey('wallet.id', link_to_name='transaction_fee', onupdate='CASCADE'), nullable=True)
    from_amount = Column(BigInteger, nullable=True)
    to_amount = Column(BigInteger, nullable=True)
    fee_amount = Column(BigInteger, nullable=True)
    notes = Column(String(500), nullable=True)
    from_txid = Column(String(100), nullable=True)
    to_txid = Column(String(100), nullable=True)

    TRANSFER = "Transfer"
    EXCHANGE = "Exchange"
    INC_MINING = "INC-Mining"
    INC_AIRDROP = "INC-Airdrop/Fork"
    INC_GIFT = "INC-Gift"
    EXP_PURCHASE = "EXP-Purchase"
    EXP_GIFT = "EXP-Gift"
    must_have_from_and_to = [TRANSFER, EXCHANGE]
    may_not_have_fee = [INC_MINING, INC_AIRDROP, INC_GIFT]
    all_trans_types = [TRANSFER, EXCHANGE, INC_MINING, INC_AIRDROP, INC_GIFT, EXP_PURCHASE, EXP_GIFT]

    @property
    def from_amount_str(self):
        if self.from_wallet:
            return self.from_wallet.currency.format_large(-self.from_amount)
        return ""

    @property
    def to_amount_str(self):
        if self.to_wallet:
            return self.to_wallet.currency.format_large(self.to_amount)
        return ""

    @property
    def fee_amount_str(self):
        if self.fee_wallet:
            return self.fee_wallet.currency.format_large(-self.fee_amount)
        return ""

    @property
    def date_utc(self):
        return self.date.replace(tzinfo=pytz.utc)

    @property
    def date_local(self):
        return self.date_utc.astimezone(local_time_zone)

    # Must call this manually, since PeeWee doesn't support field validation
    def validate_fields(self):
        if self.trans_type in Transaction.must_have_from_and_to:
            if self.from_wallet is None or self.to_wallet is None:
                raise ValidationError("Transaction type %s must have both a from and a to wallet")
        else:
            if self.from_wallet is not None and self.to_wallet is not None:
                raise ValidationError("Transaction type %s may not have both a from and a to wallet")
        if self.trans_type in Transaction.may_not_have_fee:
            if self.fee_wallet is not None:
                raise ValidationError("Transaction type %s may not have a fee specified")

    # # Overload the function so we can validate fields
    # def save(self, force_insert=False, only=None):

    # # Overload the function so we can validate fields
    # def update(self, __data=None, **update):
    #     self.validate_fields()
    #     return super().update(__data, **update)

    # # Overload the function so we can validate fields
    # def insert(self, __data=None, **insert):
    #     self.validate_fields()
    #     return super().insert(__data, **insert)

    def __str__(self):
        return "Tx #%s" % self.id


class Pair(Base):
    __tablename__ = 'pair'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    currency = Column(ForeignKey('currency.id', link_to_name='pair', onupdate='CASCADE'), nullable=False)
    ref_currency = Column(ForeignKey('currency.id', link_to_name='pair_ref', onupdate='CASCADE'), nullable=False)
    price_source = Column(String(50), nullable=False)
    last_update = Column(DateTime, nullable=False)

    def __str__(self):
        return "Pair #%s" % self.id


class Price(Base):
    __tablename__ = 'price'
    __table_args__ = (
        UniqueConstraint('pair', 'date', name='unique1'),
    )

    id = Column(Integer, primary_key=True)
    pair = Column(ForeignKey('pair.id', onupdate='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    price_open = Column(Float, nullable=False)
    price_high = Column(Float, nullable=False)
    price_low = Column(Float, nullable=False)
    price_close = Column(Float, nullable=False)

    def __str__(self):
        return "Price #%s" % self.id


Base.metadata.create_all(engine)
