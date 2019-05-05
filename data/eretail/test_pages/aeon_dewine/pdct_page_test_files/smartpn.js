function locationJump(url) {
    if (url == "" || url == undefined) {
        return false;
    }

    location.href = url;

}
/* 検索フォーム */
jQuery(function() {
    var inputKeyword = jQuery('.search_form_ input#keyword')
    /* inputKeyword.after('<p class="placeholder_">キーワードから探す</p>'); */
    var PHKeyword = jQuery('.search_form_ .placeholder_')

    inputKeyword.focus(function() {
        PHKeyword.css('display', 'none');
    });
    PHKeyword.click(function() {
        jQuery(this).css('display', 'none');
        inputKeyword.focus();
    });
    inputKeyword.blur(function() {
        var inputKeywordValue = jQuery('.search_form_ input#keyword').attr('value')
        if (inputKeywordValue == '') {
            PHKeyword.css('display', 'block');
        } else {
            PHKeyword.css('display', 'none');
        }
    });
});


/* マイページ　アドレス帳の変更用 */
jQuery(function() {
    jQuery("#dest_change #destnav").css("display", "none");
    jQuery("#dest_change a").click(function() {
        jQuery("#dest_change #destnav").slideToggle("fast", function() {
            if (jQuery("#dest_change #destnav").css("display") == "none") {
                jQuery("#dest_change a.menu_").css("background-image", "url('aeon_std/img/usr/link_mypage.png')");
            } else if (jQuery("#dest_change #destnav").css("display") == "block") {
                jQuery("#dest_change a.menu_").css("background-image", "url('aeon_std/img/usr/down_mypage.png')");
            }
        });
    });
});



//jQuery(document).ready(function() {
//    jQuery("#goods_class_filter_ select").bind("change", function(event) {
//        location.href = jQuery(this).val();
//    });
//    jQuery("#goods_class_filter_").css("display", "block");
//	var listWidth = jQuery('body').width()+"px";
//	jQuery('nav.CategoryStyleG_ ul li').css('width', listWidth);
//
//    jQuery(window).bind('load orientationchange', function() {
//        if (Math.abs(window.orientation) === 90) {
//            jQuery('meta[name=viewport]').attr('content', 'width=device-height, height=' + jQuery('body').height() + ', user-scalable=no, initial-scale=1, maximum-scale=1');
//			var listWidth = jQuery('body').width()+"px";
//			jQuery('nav.CategoryStyleG_ ul li').css('width', listWidth);
//        } else {
//            jQuery('meta[name=viewport]').attr('content', 'width=device-width, height=' + jQuery('body').height() + ', user-scalable=no, initial-scale=1, maximum-scale=1');
//			var listWidth = jQuery('body').width()+"px";
//			jQuery('nav.CategoryStyleG_ ul li').css('width', listWidth);
//        }
//    })
//	jQuery(window).resize(function(){
//		var listWidth = jQuery('body').width()+"px";
//		jQuery('nav.CategoryStyleG_ ul li').css('width', listWidth);
//	});
//});

/* 孫カテゴリ用 */
jQuery(function() {
    if (jQuery('#c_open').val() == '0') { /* カテゴリ展開時のセット */
        jQuery('nav.CategoryStyleG_').find('ul.layer1_, ul.layer2_, ul.layer3_').css('display', 'block');
        jQuery('nav.CategoryStyleG_ .parent_').toggleClass("img_hidden_");
    } else { /* カテゴリ非展開時のセット */
        jQuery('nav.CategoryStyleG_').find('ul.layer1_, ul.layer2_, ul.layer3_').css('display', 'none');
    }

    if (jQuery('#g_open').val() == '0') { /* カテゴリ展開時のセット */
        jQuery('nav.GenreStyle_').find('ul.layer1_, ul.layer2_, ul.layer3_').css('display', 'block');
        jQuery('nav.GenreStyle_ .parent_').toggleClass("img_hidden_");
    } else { /* カテゴリ非展開時のセット */
        jQuery('nav.GenreStyle_').find('ul.layer1_, ul.layer2_, ul.layer3_').css('display', 'none');
    }

    jQuery('nav.CategoryStyleG_ li, nav.GenreStyle_ li').each(function() {
        if (jQuery(this).children().get(0).tagName != 'P') {
            /* カテゴリ展開時のセット */
            jQuery(this).children('ul').css('display', 'block');
            jQuery(this).children('.parent_').toggleClass("img_hidden_");
        }
    });

    jQuery('nav.CategoryStyleG_ .parent_, nav.GenreStyle_ .parent_').click(function() {
        var _thisMenu = jQuery(this).parent().children("ul");
        _thisMenu.slideToggle('fast');
        jQuery(this).toggleClass("img_hidden_");
        return false;
    });

    jQuery('nav.CategoryStyleG_ .acparentname_, nav.GenreStyle_ .acparentname_').click(function() {
        var _thisMenu = jQuery(this).prev().parent().children("ul");
        _thisMenu.slideToggle('fast');
        jQuery(this).prev().toggleClass("img_hidden_");
        return false;
    });
    
    
});

/* 商品一覧　メニュースライド */

jQuery(document).ready(function(){
    jQuery('div.category_top_nav_ h2').click(function(){
            console.log(this);
        if (jQuery('#category_top .inner_').css('display') == 'none') {
        jQuery('#category_top .inner_').slideDown('normal');
        jQuery(this).removeClass('close_');
        jQuery(this).addClass('open_');
        } else {
        jQuery('#category_top .inner_').slideUp('normal');
        jQuery(this).removeClass('open_');
        jQuery(this).addClass('close_');
        }
    });
});


/* マイページ　メニュースライド */

jQuery(document).ready(function(){
    jQuery('#mypagenav .ttl_').click(function(){
        if (jQuery(this).next('div').css('display') == 'none') {
        jQuery(this).next('div').slideDown('normal');
        jQuery(this).children('div').removeClass('icon_close_');
        jQuery(this).children('div').addClass('icon_open_');
        } else {
        jQuery(this).next('div').slideUp('normal');
        jQuery(this).children('div').removeClass('icon_open_');
        jQuery(this).children('div').addClass('icon_close_');
        }
    });
});

/* メルマガ */

jQuery(document).ready(function(){
    jQuery('div.mail_ .other_list_ h2').click(function(){
            console.log(this);
        if (jQuery('div.mail_ .other_list_ ul').css('display') == 'none') {
        jQuery('div.mail_ .other_list_ ul').slideDown('normal');
        jQuery(this).removeClass('icon_close_');
        jQuery(this).addClass('icon_open_');
        } else {
        jQuery('div.mail_ .other_list_ ul').slideUp('normal');
        jQuery(this).removeClass('icon_open_');
        jQuery(this).addClass('icon_close_');
        }
    });
});

/*ご注文方法の指定 */
jQuery(document).ready(function(){
    if(document.getElementById("chkself") != null){
        if (jQuery("div.method_sender_ p input#chkself:checked").val()) {
        jQuery('div.form_senderinfo_ dl.method_sender2_').slideDown('normal');
        } else {
        jQuery('div.form_senderinfo_ dl.method_sender2_').slideUp('normal');
        }
    }

    jQuery('div.method_sender_ p').click(function(){
            console.log(this);
        if (jQuery("div.method_sender_ p input#chkself:checked").val()) {
        jQuery('div.form_senderinfo_ dl.method_sender2_').slideDown('normal');
        } else {
        jQuery('div.form_senderinfo_ dl.method_sender2_').slideUp('normal');
        }
    });
});


/* ご利用ガイド　メニュースライド */

jQuery(document).ready(function(){
    jQuery('#guidenav .ttl_').click(function(){
        if (jQuery(this).next('div').css('display') == 'none') {
        jQuery(this).next('div').slideDown('normal');
        jQuery(this).children('div').removeClass('icon_close_');
        jQuery(this).children('div').addClass('icon_open_');
        } else {
        jQuery(this).next('div').slideUp('normal');
        jQuery(this).children('div').removeClass('icon_open_');
        jQuery(this).children('div').addClass('icon_close_');
        }
    });
});


//検索テキスト 透かし文字
jQuery(document).ready(function(){
  $('#keyword')
    .blur(function(){
      var $$=$(this);
      if($$.val()=='' || $$.val()==$$.attr('title')){
        $$.css('color', '#999')
          .val($$.attr('title'));
      }
    })
    .focus(function(){
      var $$=$(this);
      if($$.val()==$$.attr('title')){
        $(this).css('color', '#000')
               .val('');
      }
    })
    .parents('form:first').submit(function(){
      var $$=$('#keyword');
      if($$.val()==$$.attr('title')){
        $$.triggerHandler('focus');
      }
    }).end()
    .blur();
});