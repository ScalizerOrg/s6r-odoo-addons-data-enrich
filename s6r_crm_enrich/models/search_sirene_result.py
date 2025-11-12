# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _
from odoo.osv import expression


class SearchSireneResult(models.TransientModel):
    _inherit = 'search.sirene.result'

    def _prepare_enriched_values(self, values=None):
        values = super(SearchSireneResult, self)._prepare_enriched_values(values)
        if values.get('country_id') and isinstance(values.get('country_id'), dict):
            country_val = values['country_id']
            domain = []
            if country_val.get('name'):
                domain.append([('name', '=', country_val['name'])])
            if country_val.get('code'):
                domain.append([('code', 'ilike', f"{country_val['code']}%" )])
            if len(domain) > 1:
                domain = expression.OR(domain)
            country_id = self.env['res.country'].search(domain)
            if country_id:
                values['country_id'] = country_id
            else:
                values.pop('country_id')
        return values

    def _prepare_enriched_result_values(self):
        res = super(SearchSireneResult, self)._prepare_enriched_result_values()
        m_model = self.env[self.wizard_id.model]
        res['website'] = self.website
        res['phone'] = self.phone
        res['email_from'] = self.email
        res['description'] = self.web_description
        res['web_category'] = self.web_category
        res['linkedin_url'] = self.linkedin_url
        res['capital'] = self.capital
        res['turnover'] = self.turnover
        res['owners'] = self.owners
        res['company_object'] = self.company_object
        return {k: v for k, v in res.items() if hasattr(m_model, k) and res[k]}
