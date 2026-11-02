import echopype as ep
import gc
import sys

def print_settings(raw_path):
    # Open the raw file structure
    echo_data = ep.open_raw(raw_file=raw_path, sonar_model="EK80")

    print("\n================== SONAR TRANSMISSION CHECK ==================")

    # 1. Check for the presence of the Beam_group1 group
    if "Sonar/Beam_group1" in echo_data.group_paths or "Sonar/Beam_group1" in [g.name for g in echo_data.__dict__.values() if hasattr(g, 'name')]:
        beam_group = echo_data["Sonar/Beam_group1"]
        
        # Check if backscatter data is complex (broadband) or power-only (narrowband)
        if "backscatter_r" in beam_group.data_vars or "backscatter_i" in beam_group.data_vars:
            print("DATA TYPE: Complex IQ Data (Broadband/FM)")
        elif "backscatter_power" in beam_group.data_vars or "backscatter" in beam_group.data_vars:
            print("DATA TYPE: Power-only Data (Narrowband/CW)")
        else:
            # Fallback to list what variables are actually here
            print(f"AVAILABLE VARIABLES: {list(beam_group.data_vars.keys())}")

        # 2. Check the frequencies for each channel
        for ch in beam_group.channel.values:
            print(f"\nChannel: {ch}")
            # Check transmit type directly from the beam_group variables
            if "transmit_type" in beam_group:
                # Get the transmit type for this channel (taking the first ping's value as representative)
                tx_type = str(beam_group["transmit_type"].sel(channel=ch).isel(ping_time=0).values)
                
                if tx_type == "FM":
                    print(f"BROADBAND (FM): Found frequency modulated chirp data.")
                    # If you ever parse an FM file, look for 'transmit_frequency_start' in ed.sonar['Vendor_specific'] 
                elif tx_type == "CW":
                    # Get the frequency nominal to show the user
                    f_nominal = float(beam_group["frequency_nominal"].sel(channel=ch).values)
                    print(f"NARROWBAND (CW): Single fixed frequency at {f_nominal/1000:.1f} kHz")
                else:
                    print(f"Transmit Type Flag: {tx_type}")
            else:
                print("Transmit type variable not found in this group.")

    else:
        print("Could not parse Sonar/Beam_group1. Available groups are:")
        print(echo_data)

    print("\n==============================================================")
    #Handle exception by deleting echo_data object
    del echo_data
    gc.collect()
    
def main():
    raw_path = sys.argv[1]
    print_settings(raw_path)
    
if __name__ == "__main__":
    main()