import logging
import re
import openerp

from openerp import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if version:
        actions = [import_nace, fix_nace_id]
        for action in actions:
            with openerp.api.Environment.manage():
                with openerp.registry(env.cr.dbname).cursor() as new_cr:
                    new_env = openerp.api.Environment(new_cr, env.uid, env.context)
                    action(new_env)

def import_nace(env):
    logger.info("[IMPORT res.partner.nace] download from ramon european service")
    wiz_model = env['nace.import']
    vals = wiz_model.default_get(wiz_model._fields)
    wiz = wiz_model.create(vals)
    wiz.run_import()

def fix_nace_id(env):
    logger.info("[UDPATE res.partner] Correction category_id for nace")

    data_records = env['ir.model.data'].search([
        ('model', '=', 'res.partner.category'),
        ('res_id', '!=', False),
        ('name', 'ilike', 'nace'),
        ('module', '=', 'l10n_eu_nace'),
        ])

    category_model = env['res.partner.category']
    nace_categ_ids = data_records.mapped('res_id')
    nace_categs = category_model.browse(nace_categ_ids)

    res_partners = env['res.partner'].search([
        '|', ('active', '=', True), ('active', '=', False),
        ('category_id', '!=', False),
        ('category_id', 'in', nace_categ_ids)
        ])

    for partner in res_partners:
        for category in partner.category_id:
            if category in nace_categs:
                if re.match("^\[.*\]", category.name):
                    nace_code = category.name.split("[")[1].split("]")[0]
                    nace = env['res.partner.nace'].search([('code', '=', nace_code)])
                    nace.ensure_one()
                    partner.nace_ids |= nace
    nace_categs.write({'active': False})
    data_records.unlink()
