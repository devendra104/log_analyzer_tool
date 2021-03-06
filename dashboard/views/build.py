from wtforms import Form
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import validators
from wtforms.validators import InputRequired


class JobSearchForm(Form):
    job_name = StringField(" ", [InputRequired()])
    build_number = StringField(" ", [InputRequired()])
    component_version = StringField(" ", [InputRequired()])
    submit = SubmitField("Submit")


class SearchByField(Form):
    choices = [
        ("Job-Name", "Job Name"),
        ("Build-Number", "Build Number"),
        ("Build-Status", "Build Status"),
        ("Build-Version", "Build Version"),
        ("Snap-Version", "Snap Version"),
    ]
    select = SelectField(" ", id=SelectField, choices=choices)
    search = StringField(" ", [InputRequired()])
    submit = SubmitField("Submit")


class DeleteBuildJob(Form):
    job_name = StringField(" ", [InputRequired()])
    build_number = StringField(" ", [InputRequired()])
    component_version = StringField(" ", [InputRequired()])
    submit = SubmitField("Submit")


class ValidatorName(Form):
    job_type = StringField("", validators=[validators.required()])
    upgrade_skip_check = [
        ("checks_on_build_machine", "Checks On Build Machine"),
        ("no_checks_on_build_machine", "No Checks On Build Machine"),
    ]
    skip_selection = SelectMultipleField(
        "",
        id=SelectField,
        choices=upgrade_skip_check,
        default=("no_checks_on_build_machine", "'No Checks On Build Machine'"),
    )
    job_number = StringField("")
    component_version = StringField("")
    snap_number = StringField("")
    submit = SubmitField("Submit")


class ObservationUpdate(Form):
    observation_data = TextAreaField(" ", [InputRequired()])
    submit = SubmitField("Submit")


class ReportForm(Form):
    job_category = StringField("", validators=[validators.required()])
    build_number = StringField("", validators=[validators.required()])
    job_name = StringField("", validators=[validators.required()])
    component_version = StringField("", validators=[validators.required()])
    bugzilla = StringField("")
    recipient_list = StringField("", validators=[validators.required()])
    subject_details = StringField("", validators=[validators.required()])
    message_details = TextAreaField("")
