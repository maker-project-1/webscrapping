// JavaScript Document


jQuery(function($) {
    $('.name1_').each(function() {
        var $target = $(this);
 
        // オリジナルの文章を取得する
        var html = $target.html();
 
        // 対象の要素を、高さにautoを指定し非表示で複製する
        var $clone = $target.clone();
        $clone
            .css({
                display: 'none',
                position : 'absolute',
                overflow : 'visible'
            })
            .width($target.width())
            .height('auto');
 
        // DOMを一旦追加
        $target.after($clone);
 
        // 指定した高さになるまで、1文字ずつ消去していく
        while((html.length > 0) && ($clone.height() > $target.height())) {
            html = html.substr(0, html.length - 1);
            $clone.html(html + '...');
        }
 
        // 文章を入れ替えて、複製した要素を削除する
        $target.html($clone.html());
        $clone.remove();
    });
});


jQuery(function($) {
    $('.ranking_name1_').each(function() {
        var $target = $(this);
        var html = $target.html();
        if (html.length > 42){
        	$target.html(html.substr(0,41) + '...');
	    }
    });
});

jQuery(function($) {
    $('.ranking_name2_').each(function() {
        var $target = $(this);
        var html = $target.html();
        if (html.length > 27){
        	$target.html(html.substr(0,26) + '...');
	    }
    });
});

jQuery(function($) {
    $('.ranking_name3_').each(function() {
        var $target = $(this);
        var html = $target.html();
        if (html.length > 30){
        	$target.html(html.substr(0,29) + '...');
	    }
    });
});