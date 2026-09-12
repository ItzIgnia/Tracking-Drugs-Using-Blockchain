// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract DrugTracking {

    // -----------------------------
    // Drug Status
    // -----------------------------
    enum Status {
        Manufactured,
        Shipped,
        Received,
        Dispensed
    }

    // -----------------------------
    // Drug Information
    // -----------------------------
    struct Drug {
        string drugId;
        string batchId;
        string drugName;
        string manufacturerName;

        uint256 quantity;
        uint256 manufacturingDate;
        uint256 expiryDate;
        uint256 shippingDate;   
        uint256 receivingDate;  

        address manufacturer;
        address currentOwner;

        Status status;
        bool exists;
    }

    // -----------------------------
    // Storage
    // -----------------------------
    mapping(string => Drug) private drugs;

    // -----------------------------
    // Events
    // -----------------------------

    event DrugManufactured(
        string drugId,
        string batchId,
        string drugName,
        uint256 quantity,
        address manufacturer
    );

    event DrugShipped(
        string drugId,
        address from,
        address to,
        uint256 shippingDate // Added to event
    );

    event DrugReceived(
        string drugId,
        address hospital,
        uint256 receivingDate // Added to event
    );

    event DrugDispensed(
        string drugId,
        address hospital
    );

    // -----------------------------
    // Register / Manufacture Drug
    // -----------------------------

    function manufactureDrug(
        string memory _drugId,
        string memory _batchId,
        string memory _drugName,
        string memory _manufacturerName,
        uint256 _quantity,
        uint256 _manufacturingDate,
        uint256 _expiryDate
    ) public {

        require(
            !drugs[_drugId].exists,
            "Drug already exists"
        );

        require(
            _quantity > 0,
            "Quantity must be greater than zero"
        );

        require(
            _expiryDate > _manufacturingDate,
            "Invalid expiry date"
        );

        drugs[_drugId] = Drug({
            drugId: _drugId,
            batchId: _batchId,
            drugName: _drugName,
            manufacturerName: _manufacturerName,

            quantity: _quantity,
            manufacturingDate: _manufacturingDate,
            expiryDate: _expiryDate,
            shippingDate: 0,  // Initialized to 0
            receivingDate: 0, // Initialized to 0

            manufacturer: msg.sender,
            currentOwner: msg.sender,

            status: Status.Manufactured,
            exists: true
        });

        emit DrugManufactured(
            _drugId,
            _batchId,
            _drugName,
            _quantity,
            msg.sender
        );
    }

    // -----------------------------
    // Ship Drug
    // -----------------------------

    function shipDrug(
        string memory _drugId,
        address _distributor
    ) public {

        require(
            drugs[_drugId].exists,
            "Drug does not exist"
        );

        require(
            drugs[_drugId].currentOwner == msg.sender,
            "Only current owner can ship"
        );

        require(
            drugs[_drugId].status == Status.Manufactured,
            "Drug cannot be shipped"
        );

        drugs[_drugId].currentOwner = _distributor;
        drugs[_drugId].status = Status.Shipped;
        drugs[_drugId].shippingDate = block.timestamp; 

        emit DrugShipped(
            _drugId,
            msg.sender,
            _distributor,
            block.timestamp
        );
    }

    // -----------------------------
    // Receive Drug at Hospital
    // -----------------------------

    function receiveDrug(
        string memory _drugId
    ) public {

        require(
            drugs[_drugId].exists,
            "Drug does not exist"
        );

        require(
            drugs[_drugId].currentOwner == msg.sender,
            "Only current owner can receive"
        );

        require(
            drugs[_drugId].status == Status.Shipped,
            "Drug is not in shipment"
        );

        drugs[_drugId].status = Status.Received;
        drugs[_drugId].receivingDate = block.timestamp; 

        emit DrugReceived(
            _drugId,
            msg.sender,
            block.timestamp
        );
    }


    function shipToHospital(
    string memory _drugId,
    address _hospital
    ) public {
        require(drugs[_drugId].exists, "Drug does not exist");
        require(
            drugs[_drugId].currentOwner == msg.sender,
            "Only current owner can ship"
        );
        require(
            drugs[_drugId].status == Status.Received,
            "Drug must be received before hospital shipment"
        );
        require(
            _hospital != address(0),
            "Invalid hospital address"
        );

        drugs[_drugId].currentOwner = _hospital;
        drugs[_drugId].shippingDate = block.timestamp;
        drugs[_drugId].status = Status.Shipped;

        emit DrugShipped(
            _drugId,
            msg.sender,
            _hospital,
            block.timestamp
        );
    }
    // -----------------------------
    // Dispense Drug
    // -----------------------------

    function dispenseDrug(
        string memory _drugId
    ) public {

        require(
            drugs[_drugId].exists,
            "Drug does not exist"
        );

        require(
            drugs[_drugId].currentOwner == msg.sender,
            "Only hospital can dispense"
        );

        require(
            drugs[_drugId].status == Status.Received,
            "Drug has not been received"
        );

        drugs[_drugId].status = Status.Dispensed;

        emit DrugDispensed(
            _drugId,
            msg.sender
        );
    }

    // -----------------------------
    // Get Drug Information
    // -----------------------------

function getDrug(
    string memory _drugId
)
    public view returns (Drug memory)
{
    require(
        drugs[_drugId].exists,
        "Drug does not exist"
    );

    return drugs[_drugId];
}
    // -----------------------------
    // Check Whether Drug Exists
    // -----------------------------

    function drugExists(
        string memory _drugId
    ) public view returns (bool) {

        return drugs[_drugId].exists;
    }
}