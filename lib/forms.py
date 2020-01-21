from wtforms import Form, StringField, SelectField, SubmitField, validators, \
    SelectMultipleField, TextAreaField
from wtforms.validators import InputRequired


class JobSearchForm(Form):
    choices = [
        (
            'Job-Name',
            'Job Name'
        ),
        (
            'Build-Number',
            'Build Number'
        ),
        ('Build-Status', 'Build Status')
    ]
    select = SelectField(' ', id=SelectField, choices=choices)
    search = StringField(' ', [InputRequired()])
    submit = SubmitField('Submit')


class ValidatorName(Form):
    job_name = StringField('', validators=[validators.required()])
    choices = [
        (
            'upgrade_validation',
            'Customer DB Upgrade'
        ),
        (
            'pre_upgrade',
            'Satellite and Capsule Upgrade'
        )
    ]
    upgrade_skip_check = [
        (
            "checks_on_build_machine",
            "Checks On Build Machine"
        ),
        (
            'no_checks_on_build_machine',
            'No Checks On Build Machine'
        ),
    ]
    validator_selection = SelectField(' ', id=SelectField, choices=choices)
    skip_selection = SelectMultipleField('', id=SelectField, choices=upgrade_skip_check)
    job_number = StringField('')
    component_version = StringField('')
    snap_number = StringField('')
    submit = SubmitField('Submit')


class ObservationUpdate(Form):
    observation_data = TextAreaField(' ', [InputRequired()])
    submit = SubmitField('Submit')


class CustomerName(Form):
    customer_name = StringField('', validators=[validators.required()])


class Build_Number(Form):
    build_number = StringField('', validators=[validators.required()])


class Snap_No(Form):
    snap_no = StringField('', validators=[validators.required()])


class Bugzilla_No(Form):
    bugzilla = StringField('', validators=[validators.required()])


class Mailing_List(Form):
    mailer_name = StringField('', validators=[validators.required()])


class ReportForm(Form):
    """A form for one or more addresses"""
    customer = StringField(CustomerName, [InputRequired()])
    build_no = StringField(Build_Number, [InputRequired()])
    snap_no = StringField(Snap_No, [InputRequired()])
    bugzilla = StringField(Bugzilla_No, [InputRequired()])
    recipient = StringField(Mailing_List, [InputRequired()])
    submit = SubmitField('Submit')
