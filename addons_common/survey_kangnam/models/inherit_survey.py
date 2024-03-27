from odoo import fields, models, api


class InheritSurvey(models.Model):
    _inherit = 'survey.survey'

    def _create_answer_kangnam(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True,
                               walkin=False, **additional_vals):
        """ Main entry point to get a token back or create a new one. This method
        does check for current user access in order to explicitely validate
        security.

          :param user: target user asking for a token; it might be void or a
                       public user in which case an email is welcomed;
          :param email: email of the person asking the token is no user exists;
        """
        self.check_access_rights('read')
        self.check_access_rule('read')
        answers = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts,
                                          invite_token=invite_token)

            answer_vals = {
                'survey_id': survey.id,
                'test_entry': test_entry,
                'question_ids': [(6, 0, survey._prepare_answer_questions().ids)]
            }
            if walkin:
                answer_vals['walkin_id'] = walkin
            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
            else:
                answer_vals['email'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()
            answer_vals.update(additional_vals)
            answers += answers.create(answer_vals)

        return answers

    @api.model
    def next_page_or_question_kangnam(self, register_walkin_id, user_input, page_or_question_id, go_back=False):

        service_room = register_walkin_id.service_room
        survey = user_input.survey_id

        if survey.questions_layout == 'one_page':

            return (None, False)
        elif survey.questions_layout == 'page_per_question' and survey.questions_selection == 'random':

            pages_or_questions = list(enumerate(
                user_input.question_ids
            ))
        else:

            if survey.questions_layout == 'page_per_question':
                question_ids = survey.question_ids
            else:
                # phòng ban id 8  service_room
                pages = []

                for page in survey.page_ids:
                    # if page.service_room_page.id == service_room.id:
                    if page.service_room_page.id is False or page.service_room_page.id == service_room.id:
                        pages.append(page)

                question_ids = pages

                # question_ids = survey.page_ids.filtered()
                # question_ids = survey.page_ids.filtered(lambda x: x.service_room_page.id == service_room.id)
            pages_or_questions = list(enumerate(
                question_ids
            ))

        # First page
        if page_or_question_id == 0:
            return (pages_or_questions[0][1], len(pages_or_questions) == 1)

        current_page_index = pages_or_questions.index(
            next(p for p in pages_or_questions if p[1].id == page_or_question_id))

        # All the pages have been displayed
        if current_page_index == len(pages_or_questions) - 1 and not go_back:
            return (None, False)
        # Let's get back, baby!
        elif go_back and survey.users_can_go_back:
            return (pages_or_questions[current_page_index - 1][1], False)
        else:
            # This will show the last page
            if current_page_index == len(pages_or_questions) - 2:
                return (pages_or_questions[current_page_index + 1][1], True)
            # This will show a regular page
            else:
                return (pages_or_questions[current_page_index + 1][1], False)


class SurveyUserInputs(models.Model):
    _inherit = 'survey.user_input'

    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='walkin')
