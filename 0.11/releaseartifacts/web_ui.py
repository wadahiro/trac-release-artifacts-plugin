from trac.core import *
from trac.mimeview.api import Context
from trac.web.chrome import INavigationContributor, add_stylesheet, add_script, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.util import escape, Markup
from trac.wiki.api import *
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule
from trac.wiki.formatter import Formatter
from trac.wiki.formatter import format_to_html
from trac.resource import ResourceNotFound
from trac.ticket.model import Ticket, Milestone
from trac.versioncontrol import Changeset
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol import Changeset, Node
from pkg_resources import resource_filename
from genshi.builder import tag
from genshi.filters.transform import Transformer
from datetime import datetime
from releaseartifacts.graph import GraphManager
from releaseartifacts.model import Artifact, ArtifactManager
from releaseartifacts.versioncontrol import SCMManager
from string import Template
import re

class ArtifactUI(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, ITemplateStreamFilter, IRequestFilter)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'releaseartifacts'

    def get_navigation_items(releaseartifactgraph, req):
        yield ('mainnav', 'releaseartifacts',
               tag.a('Release Artifacts', href=req.href.releaseartifacts()))

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/releaseartifacts(?:_trac)?(?:/.*)?$', req.path_info)

    def process_request(self, req):
        # switch action with parameter.
        if req.args.get('action') == 'new':
            return self._go_create(req)
        elif req.args.get('action') == 'edit':
            return self._go_edit(req)
        elif req.args.get('action') == 'save':
            return self._do_save(req)
        elif req.args.get('action') == 'showgraph':
            return self._go_graph(req)
            
        return self._go_list(req)

    def _do_save(self, req):
        return

    def _go_create(self, req):
        return 'releaseartifacts.html', data, None
        
    def _go_list(self, req):
        #search all artifacts.
        artifacts = ArtifactManager.find_all(self.env)
        
        milestones = [m for m in Milestone.select(self.env)
                      if 'MILESTONE_VIEW' in req.perm(m.resource)]
        
        #add artifacts to milestone.
        for m in milestones:
            artifacts_of_m = [artifact for artifact in artifacts
                   if artifact.milestone == m.name]
            setattr(m, 'artifacts', artifacts_of_m)
        
        data = {'milestones':milestones, 'artifacts':artifacts}        
        return 'releaseartifactgraph.html', data, None

    def _go_edit(self, req):
        return
        
    def _go_graph(self, req):
        #search all artifacts.
        artifacts = ArtifactManager.find_all(self.env)
        
        milestones = [m for m in Milestone.select(self.env)
                      if 'MILESTONE_VIEW' in req.perm(m.resource)]
        
        #add artifacts to milestone.
        for m in milestones:
            artifacts_of_m = [artifact for artifact in artifacts
                   if artifact.milestone == m.name]
            setattr(m, 'artifacts', artifacts_of_m)
        
        manager = SCMManager(self.env, req)
        nodes = manager.artifacts_to_nodes(artifacts)
        
        roots = manager.get_roots(nodes)
        
        gm = GraphManager(self.env)
        nodes = gm.to_graphnode(roots)
        
        gm.to_s(nodes)
        
        graph = gm.to_graphviz(nodes, milestones)
        
        self.env.log.info('graphviz graph:\n%s' % graph)
        
        data = {'milestones':milestones, 'artifacts':artifacts, 'graph':graph}
        return 'releaseartifactgraph.html', data, None
        
    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [resource_filename(__name__, 'htdocs')]

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        if filename == ('milestone_edit.html'):
            return self._do_filter_for_edit(req, method, filename, stream, data)
        
        if filename == ('milestone_view.html'):
            return self._do_filter_for_view(req, method, filename, stream, data)
        
        return stream

    def _do_filter_for_edit(self, req, method, filename, stream, data):
        self.log.debug('method=%s, filename=%s, data=%s' % (method, filename, data))

        artifacts = self._get_artifacts_by_milestone(req)

        fieldset = """
        <fieldset id="group_'+arInput+'">
            <legend>Artifact</legend>
            <div align="left" style="float:left">
                <label>Tag:<input type="text" name="tag" size="100" /></label>
            </div>
            <div align="right">
                <input id="delete_'+arInput+'" type="button" value="Delete" />
            </div><br />
            <label>Download URL:<input type="text" name="url" size="100" /></label>
        </fieldset>
        """
        fieldset = re.sub('"', '\\"', fieldset)
        fieldset = re.sub('\n', '', fieldset)

        js = """
        <script type='text/javascript'>
        var arInput = 0;
        var Default = arInput;
        function addInput() {
            arInput ++   
            jQuery("#area").before('%s');
            jQuery("#delete_" + arInput).click(function() {
                if(confirm('Delete?')) {
                    jQuery(this).parent().parent().remove();
                }
            });
        }
        function addArtifact(tag, url) {
            addInput();
            jQuery("#group_" + arInput + " input[@name='url']").val(url);
            jQuery("#group_" + arInput + " input[@name='tag']").val(tag);
        }
        """ % (fieldset)

        js += """
        jQuery(document).ready(function($) {"""
        
        for artifact in artifacts:
            js += """
            addArtifact('%s', '%s');
        """ % (artifact.tag, artifact.url)
        
        js += """
        });
        </script>"""
        
        # resolve keywords
        if len(artifacts) == 0:
            keywords = ''
        else:
            keywords = artifacts[0].keywords
        
        area = js + """
        <fieldset>
            <legend>Release Artifacts</legend>
            <input type="text" name="keywords" size="100" value="%s"/>
            <input type="button" onclick="addInput()" value="Add Artifact"/>
            <div id="area"/>
        </fieldset>
        """ % (keywords)

        # append fieldset
        stream = stream | Transformer('//form[@id="edit"]/div[@class="field"][1]') \
            .append(tag.div(Markup(area), id="releaseartifact_filedset"))
        
        return stream
    
    def _do_filter_for_view(self, req, method, filename, stream, data):
        
        artifacts = self._get_artifacts_by_milestone(req)
        
        if len(artifacts) == 0:
            return stream
        
        wiki = '||Tag||URL||\n'
        for artifact in artifacts:
            if artifact.url == '':
                wiki += '||[source:%s]||-||\n' % (artifact.tag)
            else:
                wiki += '||[source:%s]||[%s]||\n' % (artifact.tag, artifact.url)
        
        html = """
        <fieldset>
            <legend>Release Artifacts</legend>
            %s
            <label>Keywords:%s</label>
        </fieldset>
        """ % ( self._to_wiki(wiki, req), artifacts[0].keywords)
             
        stream = stream | Transformer('//div[@class="info"]') \
            .append(tag.div(Markup(html), id="releaseartifact_filedset"))
            
        return stream
    
    def _get_artifacts_by_milestone(self, req):
        milestone_name = self._get_milestone_name(req.path_info)
        artifacts = ArtifactManager.find_by_milestone_name(self.env, milestone_name)
        return artifacts
    
    def _get_milestone_name(self, path):
        if path.startswith('/milestone/'):
            return path.replace('/milestone/', '')
        else:
            return None
        
    def _to_wiki(self, wiki_text, req):
        return format_to_html(self.env, Context.from_request(req),
                               wiki_text)

    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        if req.method != 'POST' or req.path_info.startswith('/milestone/') == False \
            or req.args.get('action') != 'edit':
            return handler

        self._update_release_artifacts(req)

        return handler
    
    def _update_release_artifacts(self, req):
        # current name of milestone
        old_milestone_name = req.args.get('id')
        # new milestone name
        milestone_name = req.args.get('name')
        
        keywords = req.args.get('keywords')
        tags = self._to_list(req.args.get('tag'))
        urls = self._to_list(req.args.get('url'))
        
        artifacts = []
        
        count = len(tags)
        for index in range(count):
            if tags[index] == '':
                continue;
            artifact = Artifact(self.env, milestone_name, tags[index], urls[index], keywords)
            artifacts.append(artifact)

        ArtifactManager.update_all(self.env, artifacts, old_milestone_name)
                
    def _to_list(self, input):
        if input == None:
            return []
        if isinstance(input, list):
            return input
        else:
            return [input]

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/milestone/'):
            return (template, data, content_type)
            #add_stylesheet(req, 'mavenartifact/css/style.css')
            #add_script(req, 'mavenartifact/js/jquery.jec.min-0.5.2.js')
        return (template, data, content_type)

