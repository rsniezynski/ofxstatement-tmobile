#!/usr/bin/env python3

import csv
from datetime import datetime
from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.statement import generate_transaction_id
from ofxstatement import statement

class TMobilePLCSVParser(CsvStatementParser):
    date_format = "%d-%m-%Y"

    mappings = {
                "date": 0,
                "payee": 1,
                "memo": 3,
                "amount": 4,
                }

    def parse(self):
        """Parse."""
        return super(TMobilePLCSVParser, self).parse()

    def split_records(self):
        """Split records using a custom dialect."""
        return csv.reader(self.fin, delimiter=",")

    def parse_record(self, line):
        """Parse a single record."""
        # Skip initial header
        if line[0] == 'Data':
            return None
        # Currency
        amount, currency = line[4].rsplit(" ", 1)
        line[4] = amount
        line.append(currency)
        if not self.statement.currency:
            self.statement.currency = currency

        # Create statement and fixup missing parts
        # line[9] = line[9].replace(',','.')
        stmtline = super(TMobilePLCSVParser, self).parse_record(line)
        stmtline.trntype = 'DEBIT' if stmtline.amount < 0 else 'CREDIT'
        stmtline.id = generate_transaction_id(stmtline)

        # Set global statement values
        self.statement.start_date = datetime.strptime(line[0], self.date_format)
        # self.statement.start_balance = float(line[11].replace(',','.'))
        if not self.statement.end_date:
            self.statement.end_date = datetime.strptime(line[0], self.date_format)
        # if not self.statement.end_balance:
            # self.statement.end_balance = float(line[11].replace(',','.'))

        return stmtline


class TMobilePLPlugin(Plugin):
    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'utf8')
        f = open(filename, 'r', encoding=encoding)
        parser = TMobilePLCSVParser(f)
        parser.statement.account_id = self.settings['account']
        parser.statement.bank_id = self.settings.get('bank', 'Alior')
        return parser
