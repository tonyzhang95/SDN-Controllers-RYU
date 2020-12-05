from mininet.topo import Topo

class MyTopo( Topo ):

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts
        leftHost            = self.addHost( 'h1' )
        rightHost           = self.addHost( 'h2' )

        # Add switches
        leftCoreSwitch      = self.addSwitch( 's1' )
        middleCoreSwitch    = self.addSwitch( 's2' )
        rightCoreSwitch     = self.addSwitch( 's3' )
        leftEdgeSwitch      = self.addSwitch( 's4' )
        righEdgetSwitch     = self.addSwitch( 's5' )

        # Add links
        self.addLink( leftHost        , leftEdgeSwitch   , 1 , 1 )
        self.addLink( rightHost       , righEdgetSwitch  , 1 , 1 )

        self.addLink( leftEdgeSwitch  , leftCoreSwitch   , 2 , 1 )
        self.addLink( leftEdgeSwitch  , middleCoreSwitch , 3 , 1 )
        self.addLink( leftEdgeSwitch  , rightCoreSwitch  , 4 , 1 )

        self.addLink( righEdgetSwitch , leftCoreSwitch   , 2 , 2 )
        self.addLink( righEdgetSwitch , middleCoreSwitch , 3 , 2 )
        self.addLink( righEdgetSwitch , rightCoreSwitch  , 4 , 2 )


topos = { 'mytopo': ( lambda: MyTopo() ) }
