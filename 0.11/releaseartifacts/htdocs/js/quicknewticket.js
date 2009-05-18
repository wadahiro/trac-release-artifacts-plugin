
var QuickNewTicket = function(baseUrl) {
	this.baseUrl = baseUrl;
	this.newTicketUrl = baseUrl + '/newticket';
}

QuickNewTicket.prototype.openDialog = function(wikiName, summary) {
    jQuery.ajax({
        type:'GET',
        url:this.newTicketUrl,
        success:function(xml){
        	//insert New Ticket Form
            jQuery("#quicknewticket_properties").html(jQuery('#properties', xml));
            
            //set hidden value
            jQuery("#quicknewticket_target").attr("value", summary);
            jQuery("#quicknewticket_wikiName").attr("value", wikiName);
            
            //set default value
            jQuery("#field-summary").attr("value", summary);
            jQuery("#field-description").attr("value", summary);
            
            //open dialog
            jQuery("#quicknewticket_dialog").dialog("open");
        }
    });
}

var quickNewTicketObj; 

QuickNewTicket.initialize = function(baseUrl) {
    quickNewTicketObj = new QuickNewTicket(baseUrl);
    
	jQuery(document).ready(function(){
	    $("#quicknewticket_dialog").dialog({ 
	        title: 'Create New Ticket',
	        dialogClass: 'flora',
	        autoOpen: false,
	        modal: false,
	        width: 650,
	        height: 550,
	        overlay: { 
	            opacity: 0.5, 
	            background: "black" 
	        },
	        buttons: {
	            'Create': function() {
	                $("#quicknewticket_form").submit();
	            },
	            'Cancel': function() {
	                $(this).dialog('close');
	            }
	        }
	    });
	})
};

QuickNewTicket.openDialog = function(wikiName, summary) {
	quickNewTicketObj.openDialog(wikiName, summary);
}
