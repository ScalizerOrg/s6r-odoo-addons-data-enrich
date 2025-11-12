# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time
from odoo.osv import expression
from odoo.osv.expression import is_leaf

import logging

_logger = logging.getLogger(__name__)


class InseeEnrichedFieldsMixin(models.AbstractModel):
    _inherit = 'insee.enriched.fields.mixin'

    email = fields.Char()
    phone = fields.Char()
