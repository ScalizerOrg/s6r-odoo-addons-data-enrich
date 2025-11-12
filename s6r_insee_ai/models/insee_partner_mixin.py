# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import models, fields, api, _
import json
import logging

_logger = logging.getLogger(__name__)


class InseePartnerMixin(models.AbstractModel):
    _inherit = 'insee.partner.mixin'

    web_search_result = fields.Text()


    def get_company_web_search_result(self):
        search_engine_id = self.env['ai.web.search.engine'].search([], limit=1)
        query = 'entreprise %s' % self.name
        if self.country_id:
            query += ' %s' % self.country_id.name
        web_search = search_engine_id.web_search(query=query)
        if web_search:
            self.web_search_result = web_search
            return True

    def get_company_phone_web_search_result(self):
        search_engine_id = self.env['ai.web.search.engine'].search([], limit=1)
        query = 'phone %s' % self.name
        web_search = search_engine_id.web_search(query=query, limit=5)
        if web_search:
            self.web_search_result += web_search

    def get_company_email_web_search_result(self):
        search_engine_id = self.env['ai.web.search.engine'].search([], limit=1)
        query = 'email %s' % self.name
        web_search = search_engine_id.web_search(query=query, limit=5)
        if web_search:
            self.web_search_result += web_search

    def _prepare_enriched_values(self, values=None):
        if not values:
            values = {}
        if self.env.context.get('skip_ai_enrichment'):
            return super(InseePartnerMixin, self)._prepare_enriched_values(values)

        completion_domain = [('model_id.model', '=', self._name)]
        completion_id = self.env['ai.completion'].search(completion_domain, limit=1)
        try:
            if completion_id and (self.web_search_result or self.get_company_web_search_result()):
                if hasattr(self, 'phone'):
                    self.get_company_phone_web_search_result()
                if hasattr(self, 'email'):
                    self.get_company_email_web_search_result()
                res = json.loads(completion_id.create_completion(self.id), strict=False)
                values.update(res)
        except Exception as err:
            _logger.exception("Exception occurred : %s" % err, exc_info=True)
            pass
        values = super(InseePartnerMixin, self)._prepare_enriched_values(values)
        return values
