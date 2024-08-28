##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.plugin import Plugin
from litp.core.validators import ValidationError
from litp.core.task import ConfigTask, CallbackTask
from litp.core.execution_manager import CallbackExecutionException

from litp.core.litp_logging import LitpLogger
log = LitpLogger()
from os import path, makedirs
from Cheetah.Template import Template

LITP_DATA_DIR = "/var/lib/litp/plugins/cmwplugin/data"
LITP_ENV_FILE_FOLDER = LITP_DATA_DIR + "/jboss_env_variables"
TEMPLATE_FILE = "/opt/ericsson/nms/litp/lib/jboss_plugin/env_file.tmpl"


class JBossPlugin(Plugin):
    """
    LITP jboss plugin
    """

    def validate_model(self, plugin_api_context):
        """
        This method can be used to validate the model ...

        .. warning::
          Please provide a summary of the model validation performed by
          jboss here
        """
        errors = []
        clusters = plugin_api_context.query('cluster')
        for cluster in clusters:
            for service in cluster.services:
                if len(service.applications) > 1:
                    errors.append(
                        ValidationError(
                            service.get_vpath(),
                           error_message="Only one runtime should be defined."
                            "per clustered service"))

        return errors

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        *Example CLI for this plugin:*

        .. code-block:: bash

          # TODO Please provide an example CLI snippet for plugin jboss
          # here
        """
        tasks = []
        app_name = "Litp_app"

        clusters = plugin_api_context.query("cluster")

        for cluster in clusters:
            for cs in cluster.services:

                jb_containers = [app for app in cs.applications if
                        (app.is_initial() and
                         app.item_type_id == "jboss-container")]
                for app in jb_containers:
                    service_name = app.service_name

                    for node in cs.nodes:
                        tasks.append(ConfigTask(node, node,
                            'Install packages "ERIClitpmnjboss_CXP903095" '\
                            'and "EXTRlitpjbosseap_CXP903103" on node "%s" and'
                            ' create jboss service symlinks' % (node.hostname),
                            call_type="jboss::configure",
                            call_id=str(node.hostname),
                            ensure="latest",
                            service_name=service_name))

        # Callback tasks to deploy env files on MS
                active = cs.active
                for app in jb_containers:

                    tasks.append(CallbackTask(
                        cluster,
                        'Generate JBoss env files on the MS for ' +
                        'clustered service "{0}"'.format(cluster.item_id),
                        self.cb_generate_env_files,
                        active, app_name, cs.item_id, app.item_id))

        return tasks

    def _create_env_folder(self):
        if not path.exists(LITP_ENV_FILE_FOLDER):
            makedirs(LITP_ENV_FILE_FOLDER)

    def cb_generate_env_files(self, cb_api, active, app_name, cs_name,
                            jee_container_name):
        try:
            self._create_env_folder()

            for index in range(int(active)):

                unique_comp_id = cs_name + '_' + jee_container_name
                su_type = app_name + '-' + 'SuType'
                sutype_inst = su_type + '-' + str(index)
                file_name = '.'.join((unique_comp_id, sutype_inst, cs_name,
                    app_name, 'env'))
                jboss_default_file = path.join(LITP_ENV_FILE_FOLDER, file_name)

                instance_name = (cs_name + "_su_" + str(index) + "_" +
                                jee_container_name + "_instance")

                home_dir = ("/home/jboss/" + cs_name + "_su_" + str(index) +
                                "_" + jee_container_name + "_instance")

                data_dir = {"instance_name": instance_name,
                        "home_dir": home_dir}
                dataout = Template(file=TEMPLATE_FILE, searchList=[data_dir])
                open(jboss_default_file, 'w').write(str(dataout))

        except Exception, e:
            raise CallbackExecutionException("Error while generating " +
                        "JBoss env files: " + str(e))
