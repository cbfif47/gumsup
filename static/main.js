function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function validateForm() {
      let x = document.forms["mainform"]["name"].value;
      if (x == "") {
        alert("Name must be filled out");
        return false;
      }
    }
    
  function clicked(e)
    {
        if(!confirm('Are you sure?')) {
            e.preventDefault();
        }
    }

function validateCommentForm() {
      let x = document.forms["commentform"]["body"].value;
      if (x == "") {
        alert("no text in yr comment");
        return false;
      }
    }
    
  function clicked(e)
    {
        if(!confirm('Are you sure?')) {
            e.preventDefault();
        }
    }

function openSearch() {
  var search_box;
  document.getElementById("searchBox").classList.toggle("show");
  document.getElementById("search-box").focus();
}

function openType() {
  document.getElementById("typeDropdown").classList.toggle("show");
}

function openList() {
  document.getElementById("listDropdown").classList.toggle("show");
}

// Close the dropdown menu if the user clicks outside of it
    window.onclick = function(event) {
      if (!event.target.matches('.dropbtn')) {
        var dropdowns = document.getElementsByClassName("dropdown-options");
        var i;
        for (i = 0; i < dropdowns.length; i++) {
          var openDropdown = dropdowns[i];
          if (openDropdown.classList.contains('show')) {
            openDropdown.classList.remove('show');
          }
        }
      }
    }

$('.likebutton').click(function(){
    var catid;
    var newcount
    catid = $(this).attr("data-catid");
    likecount = parseInt($( '#likecount'+ catid ).text());
    $.ajax(
    {
        type:"GET",
        url: "/items/" + catid + "/like",
        data:{
                 item_id: catid
        },
        success: function( data ) 
        {
            $( '#like'+ catid ).text(data);
            if(data=='liked') {
              $( '#like'+ catid ).addClass('pressed');
              newcount = likecount + 1;
              if(newcount == 1) {
                $( '#likecount'+ catid ).text("1 like");
              } else {
                $( '#likecount'+ catid ).text(newcount + " likes");
              }
            } else {
              $( '#like'+ catid ).removeClass('pressed');
              newcount = likecount -1;
              if(newcount == 1) {
                $( '#likecount'+ catid ).text("1 like");
              } else {
                $( '#likecount'+ catid ).text(newcount + " likes");
              }
            }
        }
     })
});

$('.startbutton').click(function(){
        if(!confirm('Mark this as started?')) {
            e.preventDefault();
        }
    var catid;
    catid = $(this).attr("data-catid");
    $.ajax(
    {
        type:"GET",
        url: "/items/" + catid + "/start",
        data:{
                 item_id: catid
        },
        success: function( data ) 
        {
            $( '#start'+ catid ).addClass(data);
            $( '#rating'+ catid ).text('happening now');
        }
     })
});

$('.followbutton').click(function(){
    var username;
    username = $(this).attr("data-username");
    old_count = parseInt($( '#followers' ).text());
    $.ajax(
    {
        type:"POST",
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        url: "/users/" + username + "/follow",
        success: function( data ) 
        {
            $( '#followbutton'+ username ).text(data);
            if(data=='unfollow') {
              $( '#followers' ).text(old_count+1);
              $( '#followbutton'+ username ).addClass('pressed');
            } else if(data=='follow') {
              $( '#followers' ).text(old_count-1);
              $( '#followbutton'+ username ).removeClass('pressed');
            } else if(data=='request') {
              $( '#followbutton'+ username ).removeClass('pressed');
            } else if(data=='requested') {
              $( '#followbutton'+ username ).addClass('pressed');
            }
        }
     })
});

$(function() {

  $("#id_name_item").autocomplete({
    source: '/autocomplete-names',
    delay: 50,
    minLength: 3
  });
});

$(function() {

  $("#id_author").autocomplete({
    source: '/autocomplete-authors',
    delay: 50,
    minLength: 3
  });
});

$(function() {
  $('input[name="item_type"]').on('change', function() {
    // this, in the anonymous function, refers to the changed-<input>:
    // select the element(s) you want to show/hide:
    if(this.value=='BOOK') {
      $('input[name="author"]').attr('placeholder','(author)');
    } else if(this.value=='TV') {
      $('input[name="author"]').attr('placeholder','(season, network etc)');
    } else if(this.value=='FOOD') {
      $('input[name="author"]').attr('placeholder','(restaurant, source etc)');
    } else if(this.value=='LIFE') {
      $('input[name="author"]').attr('placeholder','(sub-title)');
    } else {
      $('input[name="author"]').attr('placeholder','(version, year etc)');
    }
  // trigger the change event, to show/hide the .business-fields element(s) on
  // page-load:
  });
});

$( function() {
    $( "#id_ended_date" ).datepicker();
    $( "#id_started_date" ).datepicker();
  } );

$('.replybutton').click(function(){
    comment_input = $( '#id_body' )
    username = $(this).attr("data-username");
    comment_input.val("@" + username + ' ');
    comment_input.focus();
    comment_input[0].setSelectionRange(1000, 1000);
});
