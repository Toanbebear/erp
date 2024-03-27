from odoo import api, fields, models, _


class NoteAccountMessageWizard(models.TransientModel):
    _name = "note.account.message.wizard"
    _description = "Thông báo"

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Text(string="Message", readonly=True, default=get_default)
