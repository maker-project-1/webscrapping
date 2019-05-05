// JavaScript Document

jQuery(function(){
	jQuery('div.feature_goods_').each(function(i){
		jQuery(this).attr('id','top_item_slide' + (i+1));
        jQuery('.flipsnap_wrapper_ .btn_flick_left').attr("disabled", "disabled");
	});
});

jQuery(function() {
    
                jQuery(".feature_goods_").each(function(){  
                    var idname = jQuery(this).attr( "id" ); 
    
                
				var ww = jQuery('#' +idname + '.feature_goods_ .flipsnap_box_' ).width();
				var maxStep = Math.ceil(jQuery('#' +idname + '.feature_goods_ .flipsnap li').length/2);
                
				jQuery('#' +idname + '.feature_goods_ .flipsnap').width(ww * maxStep);
				jQuery('#' +idname + '.feature_goods_ .flipsnap li ').width(ww/2);
				var flipsnap = Flipsnap('#' +idname + '.feature_goods_ .flipsnap', {
					distance: ww,
					maxPoint: maxStep-1
				});

                
                jQuery.each(new Array(maxStep),function(i){
                    jQuery('#' +idname + ' .pointer').append('<span></span>');
                    //console.log('.pointer');
                });
                
                jQuery('#' +idname + ' .pointer span:first').addClass('current');
                
                var $pointer = jQuery('#' +idname + ' .pointer span');
                    //console.log(idname);
                
				var $next = jQuery('#' +idname + ' .btn_flick_right').click(function() {
						flipsnap.toNext();
				});
				var $prev = jQuery('#' +idname + ' .btn_flick_left').click(function() {
						flipsnap.toPrev();
                   // console.log(this);
				});
                
				flipsnap.element.addEventListener('fspointmove', function() {
						$next.attr('disabled', !flipsnap.hasNext());
						$prev.attr('disabled', !flipsnap.hasPrev());
                        $pointer.filter('.current').removeClass('current');
                        $pointer.eq(flipsnap.currentPoint).addClass('current');
				}, false);
                
            if (maxStep == 1) {
                jQuery('#' +idname + ' .flipsnap_wrapper_ .btn_flick_right').attr("disabled", "disabled");
            }


                 
                });

});

jQuery(function() {
	jQuery('.search_form_ span').live('click',function(){
		
		if(jQuery(this).attr("class")=="search_conditional_button_"){
			jQuery(this).attr("class","search_conditional_button_open_");
		}else{
			jQuery(this).attr("class","search_conditional_button_");
		}
		jQuery('#search_conditional_area_').toggle();
	});	
});	