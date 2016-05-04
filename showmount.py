import sys
from NaServer import *
from xml.sax.saxutils import escape
from mailcap import show


no_of_args = len(sys.argv)
cmdargs = str(sys.argv)
if no_of_args != 4:
    sys.exit(1)

hostname = sys.argv[1];
username = sys.argv[2];
password = sys.argv[3];
port = 443;
serverType = "FILER"
transportType = "HTTPS"


class showmountalternative:
    """
     Private class variables
    """
    _ontapi_min_vers_   = 1.08
    _ontapi_minor_ver_  = 16
    _ontapi_major_ver_  = 1
    
    _storage_type_ = "ONTAP_7MODE"
    
    @staticmethod
    def _call_ontap_(hostname, username, password, na_cmd):
        ontap_server = NaServer(hostname, showmountalternative._ontapi_major_ver_, showmountalternative._ontapi_minor_ver_)
        ontap_server.set_server_type(serverType)
        ontap_server.set_style("LOGIN")
        ontap_server.set_admin_user(username, password)
        ontap_server.set_port(port)
        ontap_server.set_transport_type(transportType)

        na_res = None
        try:
            na_res = ontap_server.invoke_elem(na_cmd)

        except urllib2.HTTPError, http_e:
            if http_e.msg.find("Unauthorized") != -1:
                print("Authorization failure: %s" % http_e.msg)
                raise "Authorization failure: %s" % http_e.msg

            if http_e.msg.find("Not Found") != -1:
                print("Not a NetApp Filer: %s" % http_e.msg)
                raise "Not a NetApp Filer: %s" % http_e.msg

        except urllib2.URLError, url_e:
                print("URL failure: %s" % url_e.reason[1])
                raise "URL failure: %s" % url_e.reason[1]

        except Exception, na_exc:
            print("NetApp Data ONTAP Failure: %s" % na_exc)
            print("NetApp Data ONTAP Failure: " + na_res.results_reason() + "\n" )
            if not allow_failure:
                raise "NetApp Data ONTAP Failure: %s" % na_exc
            
            else:
                na_res = NaElement("results")
                print("NetApp Data ONTAP Failure: " + na_res.results_reason() + "\n" )
                na_res.attr_set("status", "failed")
                return na_res

        if na_res is not None:
            if na_res.results_status() != "passed" and not allow_failure:
                print("NetApp Data ONTAP Failure: %s" % na_res.results_status())
                print("NetApp Data ONTAP Failure: " + na_res.results_reason() + "\n" )
                raise "NetApp Data ONTAP Failure: %s" % na_res.results_status()

        else:
            na_res = NaElement("results")
            print("NetApp Data ONTAP Failure: " + na_res.results_reason() + "\n")
            na_res.attr_set("status", "failed")
            return na_res

        return na_res
    

    @staticmethod
    def export_rule_get_iter(hostname, username, password, policy):
        se_volume = None
        exp_rule_get_iter_cmd = NaElement("export-rule-get-iter")
        exp_rule_get_iter_cmd.child_add_string("max-records", "12345")
        tag_elem = NaElement("tag")
        exp_rule_get_iter_cmd.child_add(tag_elem)
        
        query = NaElement("query")
        exp_rule_get_iter_cmd.child_add(query)
        
        exp_rule_query_attrs = NaElement("export-rule-info")
        query.child_add(exp_rule_query_attrs)
        
        showmountalternative._add_query_attr(exp_rule_query_attrs, "export-rule-info", "policy-name", policy)
        
        desired_attrs = NaElement("desired-attributes")
        exp_rule_get_iter_cmd.child_add(desired_attrs)
        
        
        export_rule_info = NaElement("export-rule-info")
        desired_attrs.child_add(export_rule_info)

        showmountalternative._add_desired_attr(export_rule_info, "policy-name")
        showmountalternative._add_desired_attr(export_rule_info, "client-match")
        
        tag = None
        client_match_list = []
        while True:
            if tag is not None:
                next_tag = xml.sax.saxutils.escape(tag)
                tag_elem.set_content(next_tag)
                        
            exp_rule_get_iter_result = showmountalternative._call_ontap_(hostname, username, password, 
                                                             exp_rule_get_iter_cmd)

            if exp_rule_get_iter_result.results_status() == "passed":
                attr_list = exp_rule_get_iter_result.child_get("attributes-list");
                all_client_match = []
                client_match_list_everyone = []
                all_client_match_temp = ""
                counter_0 = 0;
                counter_1 = 0;
                for exp_rule_info in attr_list.children_get():
                    if exp_rule_info.child_get_string("policy-name") == policy:
                        client_match = exp_rule_info.child_get_string("client-match")
                        if client_match == "0.0.0.0/0":
                            client_match_list_everyone.append("(everyone)")
                            counter_0 = 1;
                        else:
                            if ( counter_1 == 0) :
                                all_client_match_temp = client_match
                                counter_1 = 1;
                            else:
                                all_client_match_temp = all_client_match_temp + "," + client_match
                                counter_1 = 2;
                if(counter_1 == 1 or counter_1 == 2 ) :
                    all_client_match.append(all_client_match_temp)
                if(counter_0 == 1) :
                    all_client_match.append(client_match_list_everyone.pop())
                return all_client_match
            #volume-get-iter with query attribute, next-tag is None   
            tag = exp_rule_get_iter_result.child_get_string("next-tag")      
            if tag is None:
                break



    @staticmethod
    def _get_storage_type(hostname, username, password):
        na_cmd = NaElement("system-get-ontapi-version")
        na_res = showmountalternative._call_ontap_(hostname, username, password, na_cmd)
        major_version = na_res.child_get_string("major-version")
        minor_version = na_res.child_get_string("minor-version")

        showmountalternative._ontapi_major_ver_ = major_version
        if minor_version > 8 and minor_version < 15:
            showmountalternative._ontapi_minor_ver_ = minor_version
            return("ONTAP_7MODE")
        elif minor_version >= 15:
            showmountalternative._ontapi_minor_ver_ = minor_version
            na_cmd = NaElement("system-get-version")
            na_res = showmountalternative._call_ontap_(hostname, username, password, na_cmd)
            if na_res.child_get_string("is-clustered") == "true" :
                return("ONTAP_CDOT")
            else:
                return("ONTAP_7MODE")
        else :
            print("OnTAPI minor version (%s) must be at least %2.2f" % (minor_version,
                                                                                                 showmountalternative._ontapi_minor_ver_))
    
    @staticmethod
    def _add_query_attr(attr_base, desired_attr, desired_key, desired_value):
        attr_elem = NaElement(desired_attr);
        attr_base.child_add(attr_elem);
        attr_elem.child_add_string(desired_key, desired_value);
    
    @staticmethod
    def _add_desired_attr(attr_base, desired_attr):
        attr_elm = NaElement(desired_attr)
        attr_base.child_add(attr_elm)
    
    @staticmethod
    def volume_get_iter(hostname, username, password):
        se_volume = None
        vol_get_iter_cmd = NaElement("volume-get-iter")
        vol_get_iter_cmd.child_add_string("max-records", "50")
        tag_elem = NaElement("tag")
        vol_get_iter_cmd.child_add(tag_elem)
        
        query = NaElement("query")
        vol_get_iter_cmd.child_add(query)
        
        vol_query_attrs = NaElement("volume-attributes")
        query.child_add(vol_query_attrs)
        
        desired_attrs = NaElement("desired-attributes")
        vol_get_iter_cmd.child_add(desired_attrs)
        vol_attrs = NaElement("volume-attributes")
        desired_attrs.child_add(vol_attrs)

        showmountalternative._add_desired_attr(vol_attrs, "volume-id-attributes")
        name_attr = vol_attrs.child_get("volume-id-attributes")
        showmountalternative._add_desired_attr(name_attr, "name")
        showmountalternative._add_desired_attr(name_attr, "junction-path")
        
        showmountalternative._add_desired_attr(vol_attrs, "volume-state-attributes")
        state_attrs = vol_attrs.child_get("volume-state-attributes")
        showmountalternative._add_desired_attr(state_attrs, "state")
        showmountalternative._add_desired_attr(state_attrs, "is-junction-active")    

        showmountalternative._add_desired_attr(vol_attrs, "volume-export-attributes")
        vol_exp_attri = vol_attrs.child_get("volume-export-attributes")
        showmountalternative._add_desired_attr(vol_exp_attri, "policy")
        
        tag = None
        while True:
            if tag is not None:
                next_tag = xml.sax.saxutils.escape(tag)
                tag_elem.set_content(next_tag)
#                 tag_elem.set_content(tag)
                        
            vol_get_iter_result = showmountalternative._call_ontap_(hostname, username, password, 
                                                             vol_get_iter_cmd)

            if vol_get_iter_result.results_status() == "passed":
                testresult = vol_get_iter_result.child_get("attributes-list")
                for vol_attri in testresult.children_get():
                    se_volume = vol_attri.child_get("volume-id-attributes").child_get_string("name")
                    junction_path = vol_attri.child_get("volume-id-attributes").child_get_string("junction-path")
                    state = vol_attri.child_get("volume-state-attributes").child_get_string("state")
                    is_junction_active = vol_attri.child_get("volume-state-attributes").child_get_string("is-junction-active")
                    if state == "online" and junction_path and is_junction_active:
                        policy = vol_attri.child_get("volume-export-attributes").child_get_string("policy")
                        client_match_list = showmountalternative.export_rule_get_iter(hostname, username, password, policy)
                        set_output = set()
                        for temp_client_match in client_match_list:
                            set_output.add(temp_client_match)
                        for client_match in set_output:
                            print '%-61s %s' % ( junction_path, client_match )
#                         print '%-61s %s' % ( junction_path, client_match_list )
                    #volume-get-iter with query attribute, next-tag is None   
            tag = vol_get_iter_result.child_get_string("next-tag")      
            if tag is None:
                break



    @staticmethod
    def volume_get_iter_specific (hostname, username, password, volume):
        counter = None
        vol_get_iter_cmd = NaElement("volume-get-iter")
        vol_get_iter_cmd.child_add_string("max-records", "50")
        tag_elem = NaElement("tag")
        vol_get_iter_cmd.child_add(tag_elem)
        
        query = NaElement("query")
        vol_get_iter_cmd.child_add(query)
        
        vol_query_attrs = NaElement("volume-attributes")
        query.child_add(vol_query_attrs)
        
        showmountalternative._add_query_attr(vol_query_attrs, "volume-id-attributes", "name", volume)
        
        desired_attrs = NaElement("desired-attributes")
        vol_get_iter_cmd.child_add(desired_attrs)
        vol_attrs = NaElement("volume-attributes")
        desired_attrs.child_add(vol_attrs)

        showmountalternative._add_desired_attr(vol_attrs, "volume-id-attributes")
        name_attr = vol_attrs.child_get("volume-id-attributes")
        showmountalternative._add_desired_attr(name_attr, "name")
        showmountalternative._add_desired_attr(name_attr, "junction-path")
        
        showmountalternative._add_desired_attr(vol_attrs, "volume-state-attributes")
        state_attrs = vol_attrs.child_get("volume-state-attributes")
        showmountalternative._add_desired_attr(state_attrs, "state")
        showmountalternative._add_desired_attr(state_attrs, "is-junction-active")    

        showmountalternative._add_desired_attr(vol_attrs, "volume-export-attributes")
        vol_exp_attri = vol_attrs.child_get("volume-export-attributes")
        showmountalternative._add_desired_attr(vol_exp_attri, "policy")

        junction_path = None        
        tag = None
        while True:
            if tag is not None:
                next_tag = xml.sax.saxutils.escape(tag)
                tag_elem.set_content(next_tag)
#                 tag_elem.set_content(tag)
                        
            vol_get_iter_result = showmountalternative._call_ontap_(hostname, username, password, 
                                                             vol_get_iter_cmd)

            if vol_get_iter_result.results_status() == "passed":
                testresult = vol_get_iter_result.child_get("attributes-list")
                for vol_attri in testresult.children_get():
                    se_volume = vol_attri.child_get("volume-id-attributes").child_get_string("name")
                    junction_path = vol_attri.child_get("volume-id-attributes").child_get_string("junction-path")
                    state = vol_attri.child_get("volume-state-attributes").child_get_string("state")
                    is_junction_active = vol_attri.child_get("volume-state-attributes").child_get_string("is-junction-active")
                    if state == "online" and junction_path and is_junction_active and se_volume == volume:
                        counter = "yes"
                        break

                    #volume-get-iter with query attribute, next-tag is None   
            tag = vol_get_iter_result.child_get_string("next-tag")      
            if tag is None:
                break

            if counter == "yes":
                print("In counter: se_volume : %s junction_path: %s " % ( se_volume, junction_path) )
                break

            counter = None
            
        return junction_path
    
    @staticmethod
    def qtree_get_iter(hostname, username, password):
        qtree_get_iter_cmd = NaElement("qtree-list-iter")
        qtree_get_iter_cmd.child_add_string("max-records", "50")
        tag_elem = NaElement("tag")
        qtree_get_iter_cmd.child_add(tag_elem)
        
        desired_attrs = NaElement("desired-attributes")
        qtree_get_iter_cmd.child_add(desired_attrs)
        qtree_info = NaElement("qtree-info")
        desired_attrs.child_add(qtree_info)

        showmountalternative._add_desired_attr(qtree_info, "volume")
        showmountalternative._add_desired_attr(qtree_info, "qtree")
        showmountalternative._add_desired_attr(qtree_info, "export-policy")
        showmountalternative._add_desired_attr(qtree_info, "export-policy-inherited")
        
        tag = None
        while True:
            if tag is not None:
                next_tag = xml.sax.saxutils.escape(tag)
                tag_elem.set_content(next_tag)
#                 tag_elem.set_content(tag)
                        
            qtree_get_iter_result = showmountalternative._call_ontap_(hostname, username, password, 
                                                             qtree_get_iter_cmd)

            if qtree_get_iter_result.results_status() == "passed":
                testresult = qtree_get_iter_result.child_get("attributes-list")
                for qtree_attri in testresult.children_get():
                    volume = qtree_attri.child_get_string("volume")
                    qtree = qtree_attri.child_get_string("qtree")
                    export_policy= qtree_attri.child_get_string("export-policy")
                    is_export_policy_inherited = qtree_attri.child_get_string("is-export-policy-inherited")

                    if ( volume != qtree and export_policy and qtree ) or ( qtree and volume != qtree and is_export_policy_inherited ):
                        # The residing volume should have the junction path, else the qtree cannnot be access from operating system even though the qtree has it's own export policy
                        junction_path = showmountalternative.volume_get_iter_specific (hostname, username, password, volume)
                        client_match_list = showmountalternative.export_rule_get_iter(hostname, username, password, export_policy)
                        set_output = set()
                        for temp_client_match in client_match_list:
                            set_output.add(temp_client_match)
                        for client_match in set_output:
                            if junction_path and client_match and qtree:
                                print('%s/%s %s' % (junction_path, qtree.ljust(54), client_match ))
                    
                    #volume-get-iter with query attribute, next-tag is None   
            tag = qtree_get_iter_result.child_get_string("next-tag")      
            if tag is None:
                break




storage_mode = showmountalternative._get_storage_type(hostname, username, password)


print ("Export list for %s:" %hostname)
showmountalternative.volume_get_iter(hostname, username, password)

if showmountalternative._ontapi_minor_ver_ >= 21:
    showmountalternative.qtree_get_iter(hostname, username, password)
