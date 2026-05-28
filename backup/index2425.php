
<!DOCTYPE html>
<html>
<head>
  	<script type= "text/javascript" src="chart.umd.js"></script>
<!--    <script src="../static/Chart.min.js"> </script> -->
        <link rel = "stylesheet" href="bestyle.css" type="text/css">
	<script src="js/chart.min.js"></script>
        <title>Geneseas Buoyancy Engine</title>
	<html lang="en">
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">

</head>

<body>
    <h1 class = "web_title">GENESEAS (RN08) BUOYANCY ENGINE 2024-25</h1>
   <title>Current Time</title>


<div class = "dive_bttn">
	<form action="buoyancymovement.py" method="post">
  		<input type="submit" value="Dive" name="dive" style="height:50px; width:150px; margin-bottom:50px; background:blue; color:white; font-size: 30px;">
	</form>
</div>


<div class = "dive_bttn">
	<form action="buoyancymovement.py" method="post">
  		<input type="submit" value="Sample" name="sample" style="height:20px; width:65px; margin-bottom:10px; background:white; color:blue; font-size: 15px;">
	</form>
</div>

<div class = "battery_bttn">
	<form action="buoyancymovement.py" method="post">
		<INPUT TYPE="submit" value="battery" name="battery">
	</form>
</div>

<?php

$file = fopen("collect_data.txt", "rb");

if(!$file){
        echo "file cant open";
        exit;
}


      

echo <<<EOF
<style>
table, td, th{
        table-layout: fixed;
        width: 100%;
        border-collapse: collapse;
        border: 3px solid black;
        text-align: center;
}
</style>
EOF;

$count = 0;
$cols = 4;
echo '<table>';

echo '<tr><th>COMPANY NAME</th><th>TIME</th><th>PRESSURE</th><th>DEPTH</th></tr>';

$depth = array();
$time = array();

if(flock($file, LOCK_EX)) {

     while(!feof($file)){ 
             $line = fgets($file);
	     $parts = explode(" : ", $line);
       	     array_push($time, $parts[1]);
       	     array_push($depth, $parts[3]);
	     echo "<tr><td height=70>$parts[0]</td><td height=70>$parts[1] s</td><td height=70>$parts[2] kPa</td><td height=70>$parts[3] m</td></tr>";
             }
             echo '</table>';
           /*  fclose($file); */

} else {
      echo "file cant open";
      exit;
}
fclose($file)
 ?>

<div style="width: 100%; max-width:600px;">
     <canvas id="myChart"></canvas>
</div>

     <script>
	var passedTime = <?php echo json_encode($time); ?>;
	var passedDepth = <?php echo json_encode($depth); ?>;

        new Chart("myChart", {
        type: "line",
        data: {
            labels: passedTime,
            datasets: [{
            fill: false,
            lineTension: 0,
            backgroundColor: "rgba(0,0,255,1.0)",
            borderColor: "rgba(0,0,255,0.1)",
            data: passedDepth
            }]
        },
        options: {
            plugins: { legend: {display: false},},
	    layout: { padding: { top: 50 } },
            scales: {
		y: {
			title: {
				display:true,
				text: 'Meters'
			}
		},
		x: {
			title: {
				display:true,
				text: 'Seconds'
			}
		}
            }
        }
        });
        </script>

<form action="buoyancymovement.py" method="post">
  <input type="submit" value="calibrate" name="calibrate">
</form>


</body>
</html>


<!--   
        const xValues = [50,60,70,80,90,100,110,120,130,140,150];
        const yValues = [7,8,8,9,9,9,10,11,14,14,15];

//	var passedDepth = <?php echo '["'.implode('", "', $depth) . '"]'?>;
	var passedTime = <?php echo '["'.implode('", "', $time) . '"]'?>;

         yAxes: [{ticks: {min: 6, max:16}}], -->

<!--
<script>
function getCurrentTime() {
	var now = new Date();
	var current_time = now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds();
	document.getElementById("current-time").innerHTML = "Current Time: " + current_time;
}
</script>
-->

<!--
<div class = "collectBtn">
	<form action="buoyancymovement.py" method="post">
		<input type="submit" value="data_collect" name="data_collect">
	</form>
</div>

<button onclick="getCurrentTime()">Get Current Time</button>
<p id="current-time"></p>



	document.write(passedTime);
	document.write(passedDepth);


-->
