# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.osv.expression import is_leaf

import logging

_logger = logging.getLogger(__name__)


class InseeEnrichedFieldsMixin(models.AbstractModel):
    _name = 'insee.enriched.fields.mixin'
    _description = 'INSEE Enriched Fields Mixin'
    _inherit = ['insee.partner.mixin']

    def _selection_partner_type(self):
        return [('company', _('Company')),
                ('association', _('Association')),
                ('administration', _('Administration')),
                ('other', _('Other'))]

    name = fields.Char()
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    siren = fields.Char('SIREN')
    siret = fields.Char('SIRET')
    nic = fields.Char('NIC')
    ape_code = fields.Char('APE Code')
    ape_label = fields.Char('APE Label')
    creation_date = fields.Date()
    country_id = fields.Many2one(string="Country", comodel_name='res.country')

    # AI Fields
    data_enriched = fields.Boolean(copy=False)
    web_description = fields.Text()
    web_category = fields.Char()
    linkedin_url = fields.Char()
    website = fields.Char()
    web_search_result = fields.Text(copy=False)
    partner_type = fields.Selection(selection=_selection_partner_type)

    # Sirene /INPI Fields
    owners = fields.Text()
    company_object = fields.Text()
    fiscal_year_closing_date = fields.Date()
    turnover = fields.Float()
    capital = fields.Float()
    net_result = fields.Float()
    debt_rate = fields.Float()
    gross_margin = fields.Float()

    # INPI - OpenData Financial Ratios
    ebe = fields.Float(string="EBE",
                       help="Measures the profitability of the company before interest, taxes, depreciation, and amortization.")
    ebit = fields.Float(string="EBIT",
                        help="Measures the profitability of the company after deducting operating costs, but before interest and taxes.")
    marge_ebe = fields.Float(string="EBE Margin", help="EBE Margin as a percentage of total revenue.")
    caf_sur_ca = fields.Float(string="Cash Flow to Revenue Ratio",
                              help="Cash Flow to Revenue Ratio expressed as a percentage.")
    ratio_de_vetuste = fields.Float(string="Obsolescence Ratio", help="Obsolescence Ratio expressed as a percentage.")
    ratio_de_liquidite = fields.Float(string="Liquidity Ratio", help="Liquidity Ratio expressed as a percentage.")
    autonomie_financiere = fields.Float(string="Financial Autonomy",
                                        help="Financial Autonomy expressed as a percentage.")
    credit_clients_jours = fields.Float(string="Average Customer Payment Period",
                                        help="Average time taken by customers to pay, expressed in days.")
    couverture_des_interets = fields.Float(string="Interest Coverage Ratio",
                                           help="Company's ability to cover its interest expenses, expressed as a percentage.")
    capacite_de_remboursement = fields.Float(string="Repayment Capacity", help="Company's ability to repay its debts.")
    credit_fournisseurs_jours = fields.Float(string="Average Supplier Payment Period",
                                             help="Average time taken to pay suppliers, expressed in days.")
    rotation_des_stocks_jours = fields.Float(string="Inventory Turnover in Days",
                                             help="Average inventory turnover period, expressed in days.")
    poids_bfr_exploitation_sur_ca = fields.Float(string="Operating Working Capital Requirement to Revenue Ratio",
                                                 help="Operating Working Capital Requirement as a percentage of revenue.")
    poids_bfr_exploitation_sur_ca_jours = fields.Float(
        string="Operating Working Capital Requirement in Days to Revenue Ratio",
        help="Operating Working Capital Requirement in days as a percentage of revenue.")
    resultat_courant_avant_impots_sur_ca = fields.Float(string="Current Result Before Tax to Revenue Ratio",
                                                        help="Current Result Before Tax as a percentage of revenue.")
