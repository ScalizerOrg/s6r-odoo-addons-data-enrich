# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from urllib.parse import quote

import logging

_logger = logging.getLogger(__name__)

OPENDATA_TOKEN = ''


class OpendataMixin(models.AbstractModel):
    _name = 'opendata.mixin'
    _description = 'Opendata Mixin'

    @api.model
    def get_opendata_token(self):
        global OPENDATA_TOKEN
        if not OPENDATA_TOKEN:
            OPENDATA_TOKEN = self.env['ir.config_parameter'].sudo().get_param('s6r_insee.opendata_key')
        return OPENDATA_TOKEN

    def opendata_explore_dataset(self, dataset_id, **kwargs):
        token = self.get_opendata_token()
        if not token:
            raise UserError(_('Opendata key must be configured in System Parameters (s6r_insee.opendata_key)'))
        parameters = '&'.join(['%s=%s' % (k, quote(str(v))) for k, v in kwargs.items()])
        url = 'https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/%s/records?%s' % (dataset_id, parameters)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Apikey %s' % token}
        res = requests.get(url, headers=headers).json()
        return res.get('results', []) if res else []

    def action_get_financial_ratios(self):
        for rec in self:
            values = rec.get_financial_ratios(rec.siren)
            rec.write(values)
        return {
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'main',
        }

    def get_financial_ratios(self, siren=None):
        if siren is None:
            siren = self.siren.replace(' ', '')
        res = self.opendata_explore_dataset('ratios_inpi_bce@opendatamef', where='siren="%s"' % siren,
                                            order_by='date_cloture_exercice desc', limit=1)
        for r in res:
            if r['siren'] == siren:
                return self._get_financial_ratios(r)
        return {}

    def _get_financial_ratios(self, result):
            values = {'turnover': result.get('chiffre_d_affaires'),
                      'net_result': result.get('resultat_net'),
                      'debt_rate': result.get('taux_d_endettement'),
                      'gross_margin': result.get('marge_brute'),
                      'fiscal_year_closing_date': result.get('date_cloture_exercice'),
                      'opendata_json_values': result}

            other_financial_fields = ['ebe', 'ebit', 'marge_ebe', 'caf_sur_ca', 'ratio_de_vetuste',
                                      'ratio_de_liquidite',
                                      'autonomie_financiere', 'credit_clients_jours',
                                      'couverture_des_interets', 'capacite_de_remboursement',
                                      'credit_fournisseurs_jours', 'rotation_des_stocks_jours',
                                      'poids_bfr_exploitation_sur_ca', 'poids_bfr_exploitation_sur_ca_jours',
                                      'resultat_courant_avant_impots_sur_ca']

            values.update({field: result.get(field) for field in other_financial_fields})
            return values
