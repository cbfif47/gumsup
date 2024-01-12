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
    catid = $(this).attr("data-catid");
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
            $( '#start'+ catid ).removeClass("tertiary-button"),
            $( '#start'+ catid ).addClass(data);
            $( '#rating'+ catid ).text('happening now');
        }
     })
});

$(function() {

  $("#id_name").autocomplete({
    source: '/autocomplete-names',
    delay: 50,
    minLength: 3
  });
});