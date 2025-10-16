<#
.SYNOPSIS
    Measures response times for one or more URLs using Invoke-WebRequest.

.DESCRIPTION
    For each supplied URL the script issues an Invoke-WebRequest call with the specified timeout
    and captures the StartTime and EndTime properties exposed on the resulting
    Microsoft.PowerShell.Commands.WebResponseObject. The total response time in seconds together
    with a success/failure flag is returned as a PSCustomObject. Errors are suppressed to the
    caller by recording the failure details in the object that is emitted for each URL.

.PARAMETER Url
    One or more URLs to request.

.PARAMETER TimeoutInSeconds
    The maximum number of seconds to wait for a response from each URL. Defaults to 30 seconds.

.EXAMPLE
    .\Test-WebResponseTime.ps1 -Url "https://learn.microsoft.com" -TimeoutInSeconds 10

    Invokes the URL with a 10 second timeout and outputs the response status and timing
    information.

.NOTES
    Requires PowerShell 7.3 or newer so that the StartTime and EndTime properties are populated
    on the WebResponseObject returned by Invoke-WebRequest.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias('Uri')]
    [ValidateNotNullOrEmpty()]
    [string[]]$Url,

    [Parameter()]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$TimeoutInSeconds = 30
)

begin {
    $results = New-Object System.Collections.Generic.List[object]
}

process {
    foreach ($currentUrl in $Url) {
        try {
            $response = Invoke-WebRequest -Uri $currentUrl -TimeoutSec $TimeoutInSeconds -ErrorAction Stop
            $elapsedSeconds = 0

            if ($null -ne $response.StartTime -and $null -ne $response.EndTime) {
                $elapsedSeconds = [Math]::Round(($response.EndTime - $response.StartTime).TotalSeconds, 3)
            }

            $results.Add([PSCustomObject]@{
                URL              = $currentUrl
                ResponseStatus   = 'Success'
                ResponseTimeSec  = $elapsedSeconds
                StatusCode       = $response.StatusCode
            }) | Out-Null
        }
        catch {
            $results.Add([PSCustomObject]@{
                URL             = $currentUrl
                ResponseStatus  = 'Failure'
                ResponseTimeSec = 0
                ErrorMessage    = $_.Exception.Message
            }) | Out-Null
        }
    }
}

end {
    return $results
}
