odoo.define('web_xls.XlsRenderer', function (require) {
	"use strict";


	var BasicRenderer = require('web.BasicRenderer');


	var XlsRenderer = BasicRenderer.extend({
		template: "XlsView",
	    className: "o_xls_view",
	    
	    init: function (parent, state, params) {
	        this._super.apply(this, arguments);
	        this.createVals = {};
	    	this.writeVals = {};
	    	this.recordsCount;
	    	this.view_fields = this.state.view_fields;
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
	    updateState: function (state, params) {
	        this.state = state;
	    	this.records = this.state.records;
    		this._deleteRecords();
	    	
	        this._renderXls();
	        return $.when();
	    },
	    _deleteRecords : function(){
	    	var s = this.sheet;
	    	for(var i=1;i<this.recordsCount+1;i++){
	    		for(var j=0;j< this.view_fields.length;j++){
	    			s.cellText(i, j, '').reRender();
		    	}
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
	    _getRows: function(text,fields,s,ri,ci){
	    		var self = this;
	    		var records = this.state.records;
	    		this.recordsCount = this.state.records.length;
	    		var fieldDetails = self._getFieldDetails(text,fields);
	    		 if(fieldDetails){
	   		 		var i=0;
				    records.forEach(function (record) {
					   
					   if (jQuery.inArray(fieldDetails.type,['boolean','date','selection','text','char','integer','float'])!== -1){
						   i=i+1;
						   s.cellText(i, ci, record[text]).reRender();
				    	}
					   else if(fieldDetails.type == 'datetime') {
					   		i=i+1;
					   		console.log("-------------------record",record);
					   		console.log("-------------------text",text);
					   		console.log("-------------------record[text]",record[text]);
					   		console.log("-------------------record[text]",typeof (record[text]));
					   		console.log("-------------------r");

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
				    return text
	    		 }
	    		
	    },
	    _getChangedValues : function (text,fields,s,ri,ci,fieldValue,fieldName) {
	    	var self = this;
	    	var createVals = this.createVals;
	    	var writeVals = this.writeVals;
	    	var records = this.state.records;
	    	
	    	console.log('this.state.records',this.state.records)
 		   if(ri>records.length){
 			   
 			   if(s.cell(0,ci) && fieldValue){
 				   var exist = false;
	    			   $.each(createVals, function(key, value) {
	    				      if (key == ri){
	    				    	  exist = true;
	    				    	  createVals[key][fieldName] = fieldValue;
	    				      }
	    				});
	    			   if (exist == false){
	    				   
	    				   createVals[ri] = {};
	    				   createVals[ri][fieldName] = fieldValue;

	    			   }
	    			   $('.xls_save').show();
 			   }
 			   
 		   }
 		   else{	
 			   if(s.cell(0,ci)){
	    			   var exist = false;
	    			   var id = records[ri-1].id
	    			   $.each(writeVals, function(key, value) {
	    				      if (key == id){
	    				    	  exist = true;
	    				    	  writeVals[id][fieldName] = fieldValue;
	    				      }
	    				});
	    			   if (exist == false){
	    				   writeVals[id] = {};
	    				   writeVals[id][fieldName] = fieldValue;
	    			   }
	    			   $('.xls_save').show();
 			   }
 		   }
	    	return [createVals,writeVals]
	    },
	   
	    _renderXls: function () {
	    	var fields = this.state.fields;
	    	var model = this.state.model_name;
	    	var view_fields = this.view_fields;
	    	var self = this;
	    	if (this.sheet){
	    		var s = this.sheet;
	    	}else{
	    		this.sheet = x_spreadsheet('#xspreadsheet');
		    	var s = this.sheet;
	    	}
	    	
	    	var i = 0;
	    	var writeVals = this.writeVals;
	    	view_fields.forEach(function (field) {
	    		s.cellText(0, i, field).reRender();
	    		self._getRows(field,fields,s,0,i);
	    		i=i+1;
	    	});
	    	
	    	   s.on('cell-edited', (text, ri, ci) => {

	    		   var fieldValue;
	    		   if(s.cell(0,ci)){
	    			   var fieldName = s.cell(0, ci).text;
	    			   if(ri==0){
	    	 			   var field = self._getRows(text,fields,s,ri,ci);
	    	 			   if (field ){
	    	 				  view_fields.push(field);
	    	 				  if( writeVals){
	    	 					 if(writeVals['0']){
			    	 				  if (jQuery.inArray(field,writeVals['0'])== -1){
			    	 					 writeVals['0'].push(field)
					    	 			   }
			    	 			   }else{
			    	 				  writeVals['0'] = [field]
			    	 			   }
	    	 				  }
	    	 				  else{
	    	 					 writeVals = {0:[field]}
	    	 				  }
	    	 			   }
	    	 			   
	    	 			   
	    	 			   $('.xls_save').show();
	    	 		   }
	    			   else{
	    				   var fieldDetails = self._getFieldDetails(fieldName,fields);
		    			   if (jQuery.inArray(fieldDetails.type,['boolean','date','selection','text','char','integer','float'])!== -1){
		    				   fieldValue = text; 
		    				    self._getChangedValues(text,fields,s,ri,ci,fieldValue,fieldName)
		    			   }
		    			   else if(fieldDetails.type == 'many2one'){
		    				   self._rpc({
					                model: fieldDetails.relation,
					                method: 'search_read',
					                fields: ['name'],
					                domain: [['name', '=', text]],
					            })
					            .then(function (result) {
					            	if (result.length){
					            		fieldValue = result[0].id
					            		 self._getChangedValues(text,fields,s,ri,ci,fieldValue,fieldName)
					            	}else{
					            		alert('Wrong Value !')
					            	}
					            	
					            });
		    			   }
	    			   }
	    			   
	    		   }else{
	    			   alert('Add column name');
	    		   }
	    		   
	    		   
	    	   });
	    	   

	    },
	    _saveData: function (e) {
	    	var model = this.state.model_name;
	    	var writeVals = this.writeVals;
	    	var createVals = this.createVals;
	    	var self = this;
	    	var records = this.state.records;
	    	var viewID = this.state.viewID;
	    	$.each(writeVals, function(key, values) {
	    		
	    		if (key == 0){
	    			self._rpc({
	 		 		   model: 'ir.ui.view',
	 		             method: 'add_field_arch',
	 		             args: [{fields:values,view_id:viewID}],
	 		 		   });
	    		}else{
		    		self._rpc({
		 		   model: model,
		             method: 'write',
		             args: [parseInt(key), values],
		 		   });
	    		}
	    	});
	    	this.writeVals = {};
	    	$.each(createVals, function(key, values) {
	    		
	    			self._rpc({
	 		 		   model: model,
	 		             method: 'create',
	 		             args: [values],
	 		 		   }).then(function (result) {
	 			    		
	 			    		values['id'] = result;
	 			    		
	 			    		records.push(values);
	 			    		
	 			    	});
	    		
		    	});
	    	this.createVals = {};
	    	$('.xls_save').hide();
	    },
	});
	return XlsRenderer;

});


	