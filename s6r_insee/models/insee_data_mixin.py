# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class InseeDataMixin(models.AbstractModel):
    _name = 'insee.data.mixin'
    _description = 'Insee Data Mixin'

    def get_idbank_series(self, idbank):
        return []
        # return insee_data.get_series(idbank)

    def get_idbank_data(self, idbank, columns):
        res = self.get_idbank_series(idbank)
        if not columns:
            columns = list(res.columns.values)
        return list(res.get(columns).itertuples())
