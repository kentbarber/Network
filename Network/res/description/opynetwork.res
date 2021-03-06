CONTAINER opynetwork
{
	NAME opynetwork;
	INCLUDE Obase;

	GROUP ID_OBJECTPROPERTIES
	{
		REAL ID_NETWORK_MAXDISTANCE { UNIT METER; MIN 0.0; }
		LONG ID_NETWORK_MAXCONNECTIONS { MIN 0; }
		BOOL ID_NETWORK_SCRAMBLER {}
		LONG ID_NETWORK_SCRAMBLESEED { MIN 0; }
		IN_EXCLUDE ID_NETWORK_INPUTLINKLIST
		{
			NUM_FLAGS 1;
			INIT_STATE 1;
			IMAGE_01_ON 300000131;
			IMAGE_01_OFF 300000130;
			SMALL_MODE_SIZE 80;
			BIG_MODE_SIZE 150;
			NEWLINE;
			ACCEPT 
			{
				Obase;
				1001381; //TP GROUP
			}
			REFUSE { }
		}
	}
	GROUP ID_NETWORK_FIELDGROUP
	{
		FIELDLIST ID_NETWORK_FIELD
		{
			ANIM ON;
			SCALE_V;
			NEWLINE;
			NODIRECTION;
			NOCOLOR;
			NOROTATION; 
		}
	}

}
