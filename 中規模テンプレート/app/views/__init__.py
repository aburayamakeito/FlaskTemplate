import re

from flask import render_template
from flask import redirect
from flask import flash
from flask.views import MethodView

camel_to_underscore = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


class ImproperlyConfigured(NotImplementedError):
    pass


class FlashMessageMixin:
    success_message = None

    def get_success_message(self):
        """
        Return the success message.
        """
        return self.success_message

    def flash_success_message(self):
        """
        Flash the success message if it's not empty.
        """
        self.flash_message('success', self.get_success_message())

    def flash_message(self, category, message):
        """
        Flash the message if it's not empty.
        """
        if message:
            flash(message, category)


class View(MethodView):
    """
    Base view for all other views. Doesn't do a whole lot.
    """

    @classmethod
    def register(cls, blueprint, route, name=None):
        """
        A shortcut method for registering this view to an app or blueprint.
        Assuming we have a blueprint and a CourseAdd view, then these two
        lines are identical in functionality:
            views.add_url_rule('/courses/add', view_func=CourseAdd.as_view('course_add'))
            CourseAdd.register(views, '/courses/add', 'course_add')
        """
        if name is None:
            # Convert 'ViewName' to 'view_name' and use it
            name = camel_to_underscore.sub(r'_\1', cls.__name__).lower()
        blueprint.add_url_rule(route, view_func=cls.as_view(name))

    def dispatch(self):
        """
        Hook for a subclass to call before dispatch actually happens.
        """
        pass

    def dispatch_request(self, *args, **kwargs):
        """
        Save args and kwargs, then dispatch the request as a normal MethodView,
        calling get() or post().
        """
        self.args = args
        self.kwargs = kwargs

        # If dispatch returns a value, use it. This most likely means it was a
        # redirect, or a custom result entirely.
        return self.dispatch() or super().dispatch_request(*args, **kwargs)

    def redirect(self, location, code=None):
        """
        Shortcut to redirect so you don't need to import flask.redirect.
        """
        return redirect(location, code)


class TemplateView(View):
    """
    A view that will simply display a template with the given context.
    """
    template_name = None

    def get_template_names(self):
        """
        Get the template_name. If this method is not overwritten, then a
        template_name variable must be declared.
        """
        if self.template_name is None:
            error = "%s must define either `template_name` or `get_template_names()`"
            raise ImproperlyConfigured(error % self.__class__.__name__)
        return self.template_name

    def get_default_context(self):
        """
        Get the default context, which contains this view instance along with
        the kwargs.
        """
        context = {
            'view': self,
            'kwargs': self.kwargs,
        }
        context.update(self.get_context())
        return context

    def get_context(self):
        """
        Hook for a sublcass to add variables to request context.
        """
        return {}

    def get(self, *args, **kwargs):
        """
        Simply render the template with the context.
        """
        return render_template(self.get_template_names(),
                               **self.get_default_context())


class RedirectView(FlashMessageMixin, View):
    """
    A view for redirecting to another URL.
    """
    url = None

    def get_url(self):
        """
        Get the success URL. If this method is not overwritten, then a
        url variable must be declared.
        """
        if self.url is None:
            error = "%s must define either `url` or `get_url()`"
            raise ImproperlyConfigured(error % self.__class__.__name__)
        return self.url

    def get(self, *args, **kwargs):
        """
        Simply redirect to the location specified.
        """
        self.flash_success_message()
        return redirect(self.get_url())


class ListView(TemplateView):
    """
    A view that will render a template with a list of objects.
    """

    model = None
    context_object_list_name = 'object_list'

    def get_context_object_list_name(self):
        """
        Get context_object_list_name.
        """
        return self.context_object_list_name

    def get_object_list(self):
        """
        Get the list of objects. If this method is not overwritten, then a
        model variable must be declared, and it must have query.all().
        """
        if self.model is None:
            error = "%s must define either `model` or `get_object_list()`"
            raise ImproperlyConfigured(error % self.__class__.__name__)
        return self.model.query.all()

    def get_default_context(self):
        """
        Add the object list to the context.
        """
        context = super().get_default_context()
        context[self.get_context_object_list_name()] = self.get_object_list()
        return context


class DetailView(TemplateView):
    """
    A view that will display details in a template for a single object.
    """
    context_object_name = 'object'

    def get_context_object_name(self):
        """
        Get context_object_name.
        """
        return self.context_object_name

    def get_object(self):
        """
        Get the object. We don't make any assumptions, so this must be
        overwritten by the subclass.
        """
        error = "%s must define `get_object()`"
        raise ImproperlyConfigured(error % self.__class__.__name__)

    def get_default_context(self):
        """
        Add the object to the context.
        """
        context = super().get_default_context()
        context[self.get_context_object_name()] = self.get_object()
        return context

    def get(self, *args, **kwargs):
        """
        Set the object to an instance variable, then process as normal.
        """
        self.object = self.get_object()
        return super().get(*args, **kwargs)


class FormView(FlashMessageMixin, TemplateView):
    """
    A view for processing a form.
    """
    context_form_name = 'form'
    form_class = None
    success_url = None

    def get_success_url(self):
        """
        Get the success URL. If this method is not overwritten, then a
        success_url variable must be declared.
        """
        if self.success_url is None:
            error = "%s must define either `success_url` or `get_success_url()`"
            raise ImproperlyConfigured(error % self.__class__.__name__)
        return self.success_url

    def get_context_form_name(self):
        """
        Get context_form_name.
        """
        return self.context_form_name

    def get_default_context(self):
        """
        Add the form to the context.
        """
        context = super().get_default_context()
        context[self.get_context_form_name()] = self.form
        return context

    def get_form(self):
        """
        Return the form instance.
        """
        return self.form_class()

    def form_valid(self):
        """
        Hook for custom processing when a form is valid. Allows for custom
        code without having to call super() in this method.
        """
        pass

    def form_valid_process(self):
        """
        Form is valid so redirect to success URL.
        """
        return redirect(self.get_success_url())

    def form_invalid(self):
        """
        Hook for custom processing when a form is invalid. Allows for custom
        code without having to call super() in this method.
        """
        pass

    def form_invalid_process(self):
        """
        Form is invalid so show it again using get().
        """
        return super().get(*self.args, **self.kwargs)

    def get(self, *args, **kwargs):
        """
        Set the form to an instance variable, then process as normal.
        """
        self.form = self.get_form()
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Set the form to an instance variable, then process as normal. If form
        is valid, then redirect. If invalid, the redisplay.
        """
        self.form = self.get_form()
        if self.form.validate_on_submit():
            # If form_valid() returns a result, use it.
            # This means subclass has custom functionality it wants to use.
            # Otherwise redirect to the success URL.
            self.flash_success_message()
            return self.form_valid() or self.form_valid_process()
        # If form_invalid() returns a result, use it.
        # This means subclass has custom functionality it wants to use.
        # Otherwise just show the form again using get().
        return self.form_invalid() or self.form_invalid_process()


class CreateView(FormView, DetailView):
    """
    A view for creating an object. Designed to work with a ModelForm.
    """

    def get_form(self):
        """
        Return the form instance with obj set.
        """
        return self.form_class(obj=self.get_object())

    def get_db_session(self):
        """
        Get the database session used to save the object. By default this is
        the session from the object query.
        """
        return self.form.obj.query.session

    def form_valid_process(self):
        """
        Save the object to the session, set the object to an instance variable,
        then process as normal (default is a redirect).
        """
        self.form.save_obj(self.get_db_session())
        self.object = self.form.obj
        return super().form_valid_process()


class UpdateView(CreateView):
    """
    A view for updating an object. Designed to work with a ModelForm.
    Works exactly the same as CreateView right now.
    """
    pass


class DeleteView(FormView, DetailView):
    """
    A view for deleting an object. Designed to work with a ModelForm.
    """

    def get_form(self):
        """
        Return the form instance with obj set.
        """
        return self.form_class(obj=self.get_object())

    def get_db_session(self):
        """
        Get the database session used to save the object. By default this is
        the session from the object query.
        """
        return self.form.obj.query.session

    def form_valid_process(self):
        """
        Delete the object in the session, remove the instance variable, then
        process as normal (default is a redirect).
        """
        self.form.delete_obj(self.get_db_session())
        self.object = None
        return super().form_valid_process()