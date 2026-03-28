import requests
import hashlib
import xml.etree.ElementTree as ET


def capture_fingerprint():
    """
    Capture fingerprint from FM220U Access L1 RD Service using CAPTURE HTTP method.
    
    Sends a CAPTURE request to the RD Service with proper XML payload and returns
    the PidData XML response containing encrypted fingerprint data.
    
    The RD Service requires:
    - HTTP Method: CAPTURE (custom method, not standard GET/POST)
    - Endpoint: https://127.0.0.1:11100/rd/capture or https://127.0.0.1:11200/rd/capture
    - Content-Type: text/xml
    - SSL Verification: Disabled (self-signed certificate)
    - Request XML with PidOptions structure
    
    Returns:
        str: PidData XML response from RD Service
    
    Raises:
        Exception: If RD Service error code is non-zero or connection fails
    """
    url = "https://127.0.0.1:11100/rd/capture"
    
    # Standard NIST-compliant PID request XML
    payload = """<PidOptions ver="1.0">
<Opts fCount="1" fType="0" iCount="0" iType="0" pCount="0" format="0" pidVer="2.0" timeout="10000" otp="" wadh="" posh="UNKNOWN" env="P"/>
<CustOpts/>
</PidOptions>"""
    
    headers = {
        "Content-Type": "text/xml"
    }
    
    try:
        # Use CAPTURE HTTP method via requests.request()
        response = requests.request(
            method="CAPTURE",
            url=url,
            data=payload,
            headers=headers,
            timeout=10,
            verify=False  # Disable SSL verification for self-signed certificate
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.ConnectionError:
        raise Exception("RD Service not available at https://127.0.0.1:11100")
    except requests.exceptions.Timeout:
        raise Exception("RD Service request timeout (10s)")
    except requests.exceptions.RequestException as e:
        raise Exception(f"RD Service error: {str(e)}")


def extract_fingerprint_template(xml_response: str):
    """
    Extract fingerprint template data from PidData XML response.
    
    Parses the XML response from RD Service to extract:
    - errCode: Error code from device (0 = success)
    - qScore: Quality score of fingerprint capture
    - Data: Encrypted biometric block (raw fingerprint data)
    
    Computes SHA256 hash of the Data field for use as unique fingerprint identifier.
    
    Args:
        xml_response (str): PidData XML string from capture_fingerprint()
    
    Returns:
        dict: {
            "status": "success" | "error",
            "fingerprint_hash": "SHA256_HEX_STRING",
            "quality_score": "0-100",
            "error_code": "0",
            "pid_data": "BASE64_ENCRYPTED_DATA"
        }
    
    Raises:
        Exception: If XML parsing fails, errCode != 0, or required fields missing
    """
    try:
        root = ET.fromstring(xml_response)
        
        # Extract Resp element attributes
        resp_elem = root.find(".//Resp")
        if resp_elem is None:
            raise Exception("Invalid RD Service response: missing Resp element")
        
        err_code = resp_elem.get("errCode", "-1")
        q_score = resp_elem.get("qScore", "0")
        
        # Check for errors
        if err_code != "0":
            error_message = resp_elem.get("errInfo", "Unknown error")
            raise Exception(f"RD Service error (errCode={err_code}): {error_message}")
        
        # Extract Data element containing encrypted fingerprint
        data_elem = root.find(".//Data")
        if data_elem is None or data_elem.text is None:
            raise Exception("No fingerprint data (Data element) in RD Service response")
        
        pid_data = data_elem.text.strip()
        
        # Compute SHA256 hash of fingerprint data for unique identification
        fingerprint_hash = hashlib.sha256(pid_data.encode()).hexdigest()
        
        return {
            "status": "success",
            "fingerprint_hash": fingerprint_hash,
            "quality_score": q_score,
            "error_code": err_code,
            "pid_data": pid_data
        }
    except ET.ParseError as e:
        raise Exception(f"Failed to parse RD Service XML response: {str(e)}")
    except Exception as e:
        raise e
