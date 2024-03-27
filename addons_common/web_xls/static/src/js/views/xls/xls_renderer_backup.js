odoo.define('web_xls.XlsRenderer', function (require) {
	"use strict";


	var AbstractRenderer = require('web.AbstractRenderer');


	var XlsRenderer = AbstractRenderer.extend({
		template: "XlsView",
	    className: "o_xls_view",
	    
	    init: function (parent, state, params) {
	        this._super.apply(this, arguments);
	        this.change = false;
	        if (params.eventTemplate) {
	            this.qweb = new QWeb(session.debug, {_s: session.origin});
	            this.qweb.add_template(utils.json_node_to_xml(params.eventTemplate));
	        }
	    },
	    start: function () {
	        this._super();
	        this.$el.on('click', '.xls_save', this._saveData.bind(this));
	    },
	    on_attach_callback: function () {
	    	if (this.isInDOM) {
	    		
	    	}
	    	else{
	    		this._renderXls();
	    		this.isInDOM = true;
	    	}
	    },
	    
	    _getFieldDetails : function(text,fields){
	    	for (const [key, value] of Object.entries(fields)) {
		    		if (key == text){
		    			return {'type':value.type,'relation':value.relation};
		    		}
    		}
	    	return false;
	    	
	    },
	    _getRows: function(records,text,fields,s,ri,ci){
	    		var self = this;
	    		var fieldDetails = self._getFieldDetails(text,fields);
	    		 if(fieldDetails){
	   		 		var i=0;
				    records.forEach(function (record) {
					   
					   if (jQuery.inArray(fieldDetails.type,['boolean','date','selection','text','char','integer','float'])!== -1){
						   i=i+1;
						   s.cellText(i, ci, record[text]).reRender();
				    		
				    	}
				    	else if(fieldDetails.type == 'many2one'){
				    		i=i+1;
				    		s.cellText(i, ci, record[text][1]).reRender();
				    	}
				    	else if(fieldDetails.type == 'one2many'){
				    		var res = "";
				    		  self._rpc({
				                model: fieldDetails.relation,
				                method: 'search_read',
				                fields: ['name'],
				                domain: [['id', 'in', record[text]]],
				            })
				            .then(function (result) {
				            	
				            	result.forEach(function (rec) {
				    	    		res = res+rec.name+'\n';
				    	    	})
				            	i=i+1;
				    	    	s.cellText(i, ci, res).reRender();
				            });
				    	}
					   
			    	});
	    		 }
	    },
	   
	    _renderXls: function () {
	    	var fields = this.state.fields;
	    	var records = this.state.records;
	    	var model = this.state.model;
	    	var view_fields = this.state.view_fields;
	    	var self = this;
	    	this.sheet = x_spreadsheet('#xspreadsheet');
	    	var s = this.sheet;
	    	var i = 0;
	    	
	    	view_fields.forEach(function (field) {
	    		s.cellText(0, i, field).reRender();
	    		self._getRows(records,field,fields,s,0,i);
	    		i=i+1;
	    	});
	    	
	    	   s.on('cell-edited', (text, ri, ci) => {
	    		   
	    		   if(ri==0){
	    			   self._getRows(records,text,fields,s,ri,ci);
	    			   $('.xls_save').prop('disabled', false);
	    		   }
	    		   
	    	   });

	    },
	    _saveData: function (e) {
//   	   s.on('cell-edited', (text, ri, ci) => {
// 		   var id = records[ri-1].id;
// 		   var field = fields[ci];
// 		   var values = {}
// 		   values[field] = text
// 		   this._rpc({
// 		   model: model,
//             method: 'write',
//             args: [id, values],
// 		   });
// 		   
// 	   });
	        console.log("-------------------save data",this.sheet);
	        console.log("-------------------cell",this.sheet.cell(0, 1));
	    },
	});
	return XlsRenderer;

});


	