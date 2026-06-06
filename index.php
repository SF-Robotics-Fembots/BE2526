<?php
chdir(__DIR__);

if ($_SERVER["REQUEST_METHOD"] === "POST") {
	if (isset($_POST["dive"])) {
		exec("cd " . escapeshellarg(__DIR__) . " && python3 main.py dive > /dev/null 2>&1 &");
		header("Location: index.php?msg=Dive+started.");
	} elseif (isset($_POST["stop"])) {
		file_put_contents(__DIR__ . "/stop_dive.request", time());
		$result = trim(shell_exec("cd " . escapeshellarg(__DIR__) . " && python3 main.py stop 2>&1"));
		file_put_contents("last_message.txt", $result);
		header("Location: index.php?msg=Program+stopped.");
	} elseif (isset($_POST["sample"])) {
		$result = trim(shell_exec("cd " . escapeshellarg(__DIR__) . " && python3 main.py sample 2>&1"));
		file_put_contents("last_message.txt", $result);
		header("Location: index.php?msg=Sample+complete.");
	} elseif (isset($_POST["battery"])) {
		$result = trim(shell_exec("cd " . escapeshellarg(__DIR__) . " && python3 main.py battery 2>&1"));
		file_put_contents("last_message.txt", $result);
		header("Location: index.php?msg=" . urlencode($result));
	}
	exit;
}

$buttonMessage = isset($_GET["msg"]) ? $_GET["msg"] : "";
?>
<!DOCTYPE html>
<html>
<head>
  	<script type= "text/javascript" src="chart.umd.js"></script>
<!--    <script src="../static/Chart.min.js"> </script> -->
        <link rel = "stylesheet" href="bestyle.css" type="text/css">
	<script src="js/chart.min.js"></script>
        <title>Geneseas Buoyancy Engine</title>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<style>
	table, td, th {
		table-layout: fixed;
		width: 100%;
		border-collapse: collapse;
		border: 3px solid black;
		text-align: center;
	}
	tr.in-window-packet td {
		background-color: #dff5df;
		border-top: 4px solid #128a28;
		border-bottom: 4px solid #128a28;
	}
	tr.in-window-packet td:first-child {
		border-left: 4px solid #128a28;
	}
	tr.in-window-packet td:last-child {
		border-right: 4px solid #128a28;
		font-weight: bold;
	}
	</style>
</head>

<body>
    <h1 class = "web_title">GENESEAS (0371A) BUOYANCY ENGINE 2025-2026</h1>
   <title>Current Time</title>


<div class = "dive_bttn">
	<form action="index.php" method="post">
  		<input type="submit" value="Dive" name="dive" style="height:50px; width:150px; margin-bottom:50px; background:blue; color:white; font-size: 30px;">
	</form>
</div>

<div class = "dive_bttn">
	<form action="index.php" method="post">
  		<input type="submit" value="Kill Program" name="stop" style="height:50px; width:180px; margin-bottom:50px; background:red; color:white; font-size: 25px;">
	</form>
</div>


<div class = "dive_bttn">
	<form action="index.php" method="post">
  		<input type="submit" value="Sample" name="sample" style="height:20px; width:65px; margin-bottom:10px; background:white; color:blue; font-size: 15px;">
	</form>
</div>

<?php
$sampleFile = "sample_data.txt";
if (file_exists($sampleFile)) {
	$sampleLine = trim(file_get_contents($sampleFile));
	$sampleParts = explode(" : ", $sampleLine);
	if (count($sampleParts) >= 6) {
		echo '<table>';
		echo '<tr><th>COMPANY NAME</th><th>TIME</th><th>BASELINE</th><th>DEPTH (TOP)</th><th>DEPTH (BOTTOM)</th><th>SAMPLE</th></tr>';
		echo '<tr><td height=70>' . htmlspecialchars($sampleParts[0]) . '</td><td height=70>' . htmlspecialchars($sampleParts[1]) . ' s</td><td height=70>' . htmlspecialchars($sampleParts[2]) . ' cm</td><td height=70>' . htmlspecialchars($sampleParts[3]) . ' cm</td><td height=70>' . htmlspecialchars($sampleParts[4]) . ' cm</td><td height=70>' . htmlspecialchars($sampleParts[5]) . '</td></tr>';
		echo '</table>';
	}
}
?>

	<div class = "battery_bttn">
		<form action="index.php" method="post">
			<INPUT TYPE="submit" value="Check Battery" name="battery">
		</form>
	</div>

<?php if ($buttonMessage !== "") { ?>
	<p><?php echo htmlspecialchars($buttonMessage); ?></p>
<?php } ?>

<?php

$dataFile = "collect_data.txt";
if (!file_exists($dataFile)) {
	touch($dataFile);
}

$file = fopen($dataFile, "rb");

if(!$file){
        echo "file cant open";
        exit;
}


      

$count = 0;
$cols = 3;
echo '<table>';

echo '<tr><th>COMPANY NAME</th><th>TIME</th><th>BASELINE</th><th>DEPTH (TOP)</th><th>DEPTH (BOTTOM)</th><th>IN WINDOW</th></tr>';

$depth = array();
$time = array();
$rows = array();

if(flock($file, LOCK_SH)) {

     while(!feof($file)){ 
             $line = fgets($file);
	     if (trim($line) === "") {
		     continue;
	     }
	     $parts = explode(" : ", $line);
	     if (count($parts) < 6) {
		     continue;
	     }
       	     array_push($time, $parts[1]);
       	     array_push($depth, $parts[2]);
	     $inWindowText = trim($parts[5]);
	     $inWindowCount = intval(explode("/", $inWindowText)[0]);
	     $rows[] = array(
		     "parts" => $parts,
		     "in_window_text" => $inWindowText,
		     "in_window_count" => $inWindowCount,
		     "highlight" => false,
	     );
             }

	     $requiredPackets = 7;
	     for ($i = 0; $i < count($rows); $i++) {
		     if ($rows[$i]["in_window_count"] === $requiredPackets) {
			     $start = $i - ($requiredPackets - 1);
			     $isConsecutiveRun = $start >= 0;

			     for ($j = $start; $j <= $i && $isConsecutiveRun; $j++) {
				     $expectedCount = $j - $start + 1;
				     if ($rows[$j]["in_window_count"] !== $expectedCount) {
					     $isConsecutiveRun = false;
				     }
			     }

			     if ($isConsecutiveRun) {
				     for ($j = $start; $j <= $i; $j++) {
					     $rows[$j]["highlight"] = true;
				     }
			     }
		     }
	     }

	     foreach ($rows as $row) {
		     $parts = $row["parts"];
		     $rowClass = $row["highlight"] ? ' class="in-window-packet"' : '';
		     echo '<tr' . $rowClass . '><td height=70>' . htmlspecialchars($parts[0]) . '</td><td height=70>' . htmlspecialchars($parts[1]) . ' s</td><td height=70>' . htmlspecialchars($parts[2]) . ' cm</td><td height=70>' . htmlspecialchars($parts[3]) . ' cm</td><td height=70>' . htmlspecialchars($parts[4]) . ' cm</td><td height=70>' . htmlspecialchars($row["in_window_text"]) . '</td></tr>';
	     }
             echo '</table>';
           /*  fclose($file); */

} else {
      echo "file cant open";
      exit;
}
fclose($file);
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
