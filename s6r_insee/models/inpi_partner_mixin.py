# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import re
import requests
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

INPI_TOKEN = ''


class InpiPartnerMixin(models.AbstractModel):
    _name = 'inpi.partner.mixin'
    _description = 'INPI Partner Mixin'

    inpi_attachment_ids = fields.Many2many('inpi.attachment', string='INPI Attachments', readonly=True)
    inpi_json_values = fields.Json(copy=False)

    @api.model
    def inpi_base_url(self):
        return 'https://registre-national-entreprises.inpi.fr'

    @api.model
    def get_inpi_token(self, refresh=False):
        global INPI_TOKEN
        if INPI_TOKEN and not refresh:
            return INPI_TOKEN
        return self.init_inpi_connection()

    @api.model
    def init_inpi_connection(self):
        global INPI_TOKEN
        inpi_username = self.env['ir.config_parameter'].sudo().get_param('s6r_insee.inpi_username')
        inpi_password = self.env['ir.config_parameter'].sudo().get_param('s6r_insee.inpi_password')
        if not inpi_username or not inpi_password:
            raise UserError(_('INPI username and password must be configured in System Parameters '
                              '(s6r_insee.inpi_username and s6r_insee.inpi_password)'))

        url = '%s/api/sso/login' % self.inpi_base_url()
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        data = {'username': inpi_username,
                'password': inpi_password}

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            token = response.json().get('token')
            if not token:
                raise UserError(_('Failed to get token from INPI API'))
            INPI_TOKEN = token
            _logger.info('Successfully obtained INPI token')
            return token
        except requests.exceptions.RequestException as e:
            INPI_TOKEN = ''
            _logger.error('Error connecting to INPI API: %s', str(e))
            raise UserError(_('Error connecting to INPI API: %s') % str(e))

    @api.model
    def get_inpi_company_data(self, siren=False):
        if not siren and hasattr(self, 'siren'):
            siren = self.siren.replace(' ', '')
        token = self.get_inpi_token()
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json',
                   'Authorization': 'Bearer %s' % token}

        url = '%s/api/companies/%s' % (self.inpi_base_url(), siren)
        res = requests.get(url, headers=headers).json()
        moral_person = res.get('formality', {}).get('content', {}).get('personneMorale', {})
        if moral_person:
            res['objet'] = moral_person.get('identite', {}).get('description', {}).get('objet')
        address = moral_person.get('adresseEntreprise', {}).get('adresse', {})
        if address:
            res['address'] = self.inpi_address_to_values(address)
        capital = moral_person.get('identite', {}).get('description', {}).get('montantCapital', 0)
        owners = moral_person.get('composition', {}).get('pouvoirs', [])
        owner_name_list = []
        for owner in owners:
            if owner['typeDePersonne'] == 'INDIVIDU':
                person = owner.get('individu', {}).get('descriptionPersonne', {})
                owner_name = person.get('nom', '')
                owner_prenom = ' '.join(person.get('prenoms', []))
                owner_name_list.append('%s %s' % (owner_name, owner_prenom.capitalize()))
            elif owner['typeDePersonne'] == 'ENTREPRISE':
                enterprise = owner.get('entreprise', {})
                name = enterprise.get('denomination', '')
                if enterprise.get('siren', ''):
                    name = '%s (%s)' % (name, enterprise['siren'])
                owner_name_list.append(name)
            else:
                _logger.info('Owner type not supported: %s', owner['typeDePersonne'])
        res['owners'] = '\n'.join(owner_name_list)
        res['capital'] = capital
        return res

    @api.model
    def inpi_address_to_values(self, address):
        address_values = {}
        address_values['street'] = ""
        if address.get('numVoiePresent', ''):
            address_values['street'] += address.get('numVoie', '')

        if address.get('typeVoiePresent', ''):
            if address_values['street']:
                address_values['street'] += ' '
            address_values['street'] += address.get('typeVoie', '')

        if address.get('voiePresent', ''):
            if address_values['street']:
                address_values['street'] += ' '
            address_values['street'] += address.get('voie', '')

        if address.get('codePostal', ''):
            address_values['zip'] = address['codePostal']
        if address.get('commune', ''):
            address_values['city'] = address['commune']
        if address.get('complementLocalisation', ''):
            address_values['street2'] = address['complementLocalisation']
        return address_values

    @api.model
    def get_inpi_company_attachments(self, siren=False):
        if not siren and hasattr(self, 'siren'):
            siren = self.siren.replace(' ', '')
        token = self.get_inpi_token()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }

        url = '%s/api/companies/%s/attachments' % (self.inpi_base_url(), siren)
        res = requests.get(url, headers=headers).json()
        return res

    @api.model
    def download_inpi_attachment(self, attachment_type, attachment_id):
        token = self.get_inpi_token()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }

        url = '%s/api/%s/%s/download' % (self.inpi_base_url(), attachment_type, attachment_id)
        res = requests.get(url, headers=headers).content
        return res

    @api.model
    def get_inpi_company_entry_balances(self, attachment_id):

        token = self.get_inpi_token()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }

        url = '%s/api/bilans-saisis/%s' % (self.inpi_base_url(), attachment_id)
        res = requests.get(url, headers=headers).json()
        return res

    @api.model
    def get_inpi_company_last_entry_balance(self, siren=False):
        if not siren and hasattr(self, 'siren'):
            siren = self.siren.replace(' ', '')
        attachments = self.get_inpi_company_attachments(siren)
        if not attachments:
            return {}
        balances = attachments.get('bilans', []) or attachments.get('bilansSaisis', [])
        if balances:
            last_attachment = balances[-1]
            balance = self.get_inpi_company_entry_balances(last_attachment['id'])
            res = {
                'balance': balance,
                'attachment': last_attachment,
            }
            return res

    @api.model
    def get_inpi_company_attachments_values(self, siren=False):
        if not siren and hasattr(self, 'siren'):
            siren = self.siren
        attachments = self.get_inpi_company_attachments(siren)
        documents = []
        for attachment_type in ['actes', 'bilans', 'bilans-saisis']:
            if attachments.get(attachment_type):
                attachments_values = [self._inpi_attachment_values(attachment_type, a) for a in
                                      attachments.get(attachment_type)]
                documents.extend(attachments_values)
        return documents

    @api.model
    def _inpi_attachment_values(self, attachment_type, attachment):
        type_rdd = attachment.get('typeRdd', [])
        attachment_description = ''
        if attachment_type != 'actes':
            attachment_description = attachment.get('libelle', '') or attachment.get('denomination', '')
            if attachment.get('dateCloture'):
                attachment_description = '%s - %s' % (attachment_description, attachment['dateCloture'])
        if not attachment_description:
            description_list = []
            for el in type_rdd:
                line_description = ' : '.join(filter(None, [el.get('typeActe', ''), el.get('decision', '')]))
                description_list.append(line_description)
            attachment_description = '\n'.join(description_list)
        attachment_date = attachment.get('dateDepot', False)
        if not attachment_date:
            attachment_date = attachment.get('updatedAt', '')[:10]

        return {'key': attachment['id'],
                'attachment_date': attachment_date,
                'name': attachment_description,
                'type': attachment_type}

    def action_get_inpi_company_attachments(self):
        self.ensure_one()
        values = self.get_inpi_company_attachments_values()
        inpi_attachment_ids = [(5,)]
        inpi_attachment_ids.extend([(0, 0, v) for v in values])
        self.write({'inpi_attachment_ids': inpi_attachment_ids})
        action = {
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'main',
        }
        return action

    def action_get_inpi_company_data(self):
        for rec in self:
            res = rec.get_inpi_company_data(rec.siren.replace(' ', ''))
            values = {'owners': res.get('owners', ''),
                      'capital': res.get('capital', 0),
                      'company_object': res.get('objet', ''),
                      'inpi_json_values': res}
            if res.get('address'):
                address = res['address']
                if not self.street:
                    values['street'] = address.get('street', '')
                if not self.street2:
                    values['street2'] = address.get('street2', '')
                if not self.zip:
                    values['zip'] = address.get('zip', '')
                if not self.city:
                    values['city'] = address.get('city', '')
            rec.write(values)
        return {
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'main',
        }
